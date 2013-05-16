# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Jonas Borgström <jonas@edgewall.com>

try:
    from base64 import b64decode
except ImportError:
    from base64 import decodestring as b64decode
try:
    import threading
except ImportError:
    import dummy_threading as threading
import os
import re
import sys
import time
import urllib2

from genshi.builder import tag

from trac.config import BoolOption
from trac.core import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.util import hex_entropy, md5, md5crypt


class LoginModule(Component):
    """Implements user authentication based on HTTP authentication provided by
    the web-server, combined with cookies for communicating the login
    information across the whole site.

    This mechanism expects that the web-server is setup so that a request to the
    path '/login' requires authentication (such as Basic or Digest). The login
    name is then stored in the database and associated with a unique key that
    gets passed back to the user agent using the 'trac_auth' cookie. This cookie
    is used to identify the user in subsequent requests to non-protected
    resources.
    """

    implements(IAuthenticator, INavigationContributor, IRequestHandler)

    check_ip = BoolOption('trac', 'check_auth_ip', 'false',
         """Whether the IP address of the user should be checked for
         authentication (''since 0.9'').""")

    ignore_case = BoolOption('trac', 'ignore_auth_case', 'false',
        """Whether login names should be converted to lower case
        (''since 0.9'').""")

    # IAuthenticator methods

    def authenticate(self, req):
        authname = None
        if req.remote_user:
            authname = req.remote_user
        elif req.incookie.has_key('trac_auth'):
            authname = self._get_name_for_cookie(req, req.incookie['trac_auth'])

        if not authname:
            return None

        if self.ignore_case:
            authname = authname.lower()

        return authname

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield ('metanav', 'login', 'logged in as %s' % req.authname)
            yield ('metanav', 'logout',
                   tag.a('Logout', href='http://code.taobao.org/logout'))
        else:
            yield ('metanav', 'login',
                   tag.a('Login', href="http://code.taobao.org/login?next="+req.base_path+req.path_info))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match('/(login|logout)/?$', req.path_info)

    def process_request(self, req):
        if req.path_info.startswith('/login'):
            self._do_login(req)
        elif req.path_info.startswith('/logout'):
            self._do_logout(req)
        self._redirect_back(req)

    # Internal methods

    def _do_login(self, req):
        """Log the remote user in.

        This function expects to be called when the remote user name is
        available. The user name is inserted into the `auth_cookie` table and a
        cookie identifying the user on subsequent requests is sent back to the
        client.

        If the Authenticator was created with `ignore_case` set to true, then 
        the authentication name passed from the web server in req.remote_user
        will be converted to lower case before being used. This is to avoid
        problems on installations authenticating against Windows which is not
        case sensitive regarding user names and domain names
        """
        if not req.remote_user:
            raise TracError(tag("Authentication information not available. "
                                "Please refer to the ",
                                tag.a('installation documentation',
                                      title="Configuring Authentication",
                                      href=req.href.wiki('TracInstall') +
                                      "#ConfiguringAuthentication"), "."))
        remote_user = req.remote_user
        if self.ignore_case:
            remote_user = remote_user.lower()

        assert req.authname in ('anonymous', remote_user), \
               'Already logged in as %s.' % req.authname

        cookie = hex_entropy()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO auth_cookie (cookie,name,ipnr,time) "
                       "VALUES (%s, %s, %s, %s)", (cookie, remote_user,
                       req.remote_addr, int(time.time())))
        db.commit()

        req.authname = remote_user
        req.outcookie['trac_auth'] = cookie
        req.outcookie['trac_auth']['path'] = req.base_path or '/'
        if self.env.secure_cookies:
            req.outcookie['trac_auth']['secure'] = True

    def _do_logout(self, req):
        """Log the user out.

        Simply deletes the corresponding record from the auth_cookie table.
        """
        if req.authname == 'anonymous':
            # Not logged in
            return

        # While deleting this cookie we also take the opportunity to delete
        # cookies older than 10 days
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM auth_cookie WHERE name=%s OR time < %s",
                       (req.authname, int(time.time()) - 86400 * 10))
        db.commit()
        self._expire_cookie(req)
        custom_redirect = self.config['metanav'].get('logout.redirect')
        if custom_redirect:
            if not re.match(r'https?:|/', custom_redirect):
                custom_redirect = req.href(custom_redirect)
            req.redirect(custom_redirect)

    def _expire_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past.
        """
        req.outcookie['trac_auth'] = ''
        req.outcookie['trac_auth']['path'] = req.base_path or '/'
        req.outcookie['trac_auth']['expires'] = -10000
        if self.env.secure_cookies:
            req.outcookie['trac_auth']['secure'] = True

    def _get_name_for_cookie(self, req, cookie):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if self.check_ip:
            cursor.execute("SELECT name FROM auth_cookie "
                           "WHERE cookie=%s AND ipnr=%s",
                           (cookie.value, req.remote_addr))
        else:
            cursor.execute("SELECT name FROM auth_cookie WHERE cookie=%s",
                           (cookie.value,))
        row = cursor.fetchone()
        if not row:
            # The cookie is invalid (or has been purged from the database), so
            # tell the user agent to drop it as it is invalid
            self._expire_cookie(req)
            return None

        return row[0]

    def _redirect_back(self, req):
        """Redirect the user back to the URL she came from."""
        referer = self._referer(req)
        if referer and not (referer == req.base_url or \
                referer.startswith(req.base_url.rstrip('/')+'/')):
            # only redirect to referer if it is from the same site
            referer = None
        req.redirect(referer or req.abs_href())

    def _referer(self, req):
        return req.args.get('referer') or req.get_header('Referer')


class HTTPAuthentication(object):

    def do_auth(self, environ, start_response):
        raise NotImplementedError


class PasswordFileAuthentication(HTTPAuthentication):
    def __init__(self, filename):
        self.filename = filename
        self.mtime = os.stat(filename).st_mtime
        self.load(self.filename)
        self._lock = threading.Lock()

    def check_reload(self):
        self._lock.acquire()
        try:
            mtime = os.stat(self.filename).st_mtime
            if mtime > self.mtime:
                self.mtime = mtime
                self.load(self.filename)
        finally:
            self._lock.release()

class BasicAuthentication(PasswordFileAuthentication):

    def __init__(self, htpasswd, realm):
        self.realm = realm
        try:
            import crypt
            self.crypt = crypt.crypt
        except ImportError:
            try:
                import fcrypt
                self.crypt = fcrypt.crypt
            except ImportError:
                self.crypt = None
        PasswordFileAuthentication.__init__(self, htpasswd)

    def load(self, filename):
        self.hash = {}
        fd = open(filename, 'r')
        for line in fd:
            line = line.strip()
            if not line:
                continue
            try:
                u, h = line.split(':')
            except ValueError:
                print >>sys.stderr, 'Warning: invalid password line in %s: %s' \
                                    % (filename, line)
                continue
            if '$' in h or self.crypt:
                self.hash[u] = h
            else:
                print >>sys.stderr, 'Warning: cannot parse password for ' \
                                    'user "%s" without the "crypt" module' % u

        if self.hash == {}:
            print >> sys.stderr, "Warning: found no users in file:", filename

    def test(self, user, password):
        self.check_reload()
        the_hash = self.hash.get(user)
        if the_hash is None:
            return False

        if not '$' in the_hash:
            return self.crypt(password, the_hash[:2]) == the_hash

        magic, salt = the_hash[1:].split('$')[:2]
        magic = '$' + magic + '$'
        return md5crypt(password, salt, magic) == the_hash

    def do_auth(self, environ, start_response):
        header = environ.get('HTTP_AUTHORIZATION')
        if header and header.startswith('Basic'):
            auth = b64decode(header[6:]).split(':')
            if len(auth) == 2:
                user, password = auth
                if self.test(user, password):
                    return user

        start_response('401 Unauthorized',
                       [('WWW-Authenticate', 'Basic realm="%s"' % self.realm),
                        ('Content-Length', '0')])('')


class DigestAuthentication(PasswordFileAuthentication):
    """A simple HTTP digest authentication implementation (RFC 2617)."""

    MAX_NONCES = 100

    def __init__(self, htdigest, realm):
        self.active_nonces = []
        self.realm = realm
        PasswordFileAuthentication.__init__(self, htdigest)

    def load(self, filename):
        """Load account information from apache style htdigest files, only
        users from the specified realm are used
        """
        self.hash = {}
        fd = open(filename, 'r')
        for line in fd.readlines():
            line = line.strip()
            if not line:
                continue
            try:
                u, r, a1 = line.split(':')
            except ValueError:
                print >>sys.stderr, 'Warning: invalid digest line in %s: %s' \
                                    % (filename, line)
                continue
            if r == self.realm:
                self.hash[u] = a1
        if self.hash == {}:
            print >> sys.stderr, "Warning: found no users in realm:", self.realm
        
    def parse_auth_header(self, authorization):
        values = {}
        for value in urllib2.parse_http_list(authorization):
            n, v = value.split('=', 1)
            if v[0] == '"' and v[-1] == '"':
                values[n] = v[1:-1]
            else:
                values[n] = v
        return values

    def send_auth_request(self, environ, start_response, stale='false'):
        """Send a digest challange to the browser. Record used nonces
        to avoid replay attacks.
        """
        nonce = hex_entropy()
        self.active_nonces.append(nonce)
        if len(self.active_nonces) > self.MAX_NONCES:
            self.active_nonces = self.active_nonces[-self.MAX_NONCES:]
        start_response('401 Unauthorized',
                       [('WWW-Authenticate',
                        'Digest realm="%s", nonce="%s", qop="auth", stale="%s"'
                        % (self.realm, nonce, stale)),
                        ('Content-Length', '0')])('')

    def do_auth(self, environ, start_response):
        header = environ.get('HTTP_AUTHORIZATION')
        if not header or not header.startswith('Digest'):
            self.send_auth_request(environ, start_response)
            return None

        auth = self.parse_auth_header(header[7:])
        required_keys = ['username', 'realm', 'nonce', 'uri', 'response',
                         'nc', 'cnonce']
        # Invalid response?
        for key in required_keys:
            if not auth.has_key(key):
                self.send_auth_request(environ, start_response)
                return None
        # Unknown user?
        self.check_reload()
        if not self.hash.has_key(auth['username']):
            self.send_auth_request(environ, start_response)
            return None

        kd = lambda x: md5(':'.join(x)).hexdigest()
        a1 = self.hash[auth['username']]
        a2 = kd([environ['REQUEST_METHOD'], auth['uri']])
        # Is the response correct?
        correct = kd([a1, auth['nonce'], auth['nc'],
                      auth['cnonce'], auth['qop'], a2])
        if auth['response'] != correct:
            self.send_auth_request(environ, start_response)
            return None
        # Is the nonce active, if not ask the client to use a new one
        if not auth['nonce'] in self.active_nonces:
            self.send_auth_request(environ, start_response, stale='true')
            return None
        self.active_nonces.remove(auth['nonce'])
        return auth['username']
