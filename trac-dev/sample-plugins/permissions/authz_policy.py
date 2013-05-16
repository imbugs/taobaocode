# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009 Edgewall Software
# Copyright (C) 2007 Alec Thomas <alec@swapoff.org>
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
# Author: Alec Thomas <alec@swapoff.org>

revision = "$Rev: 7889 $"
url = "$URL: http://svn.edgewall.org/repos/trac/tags/trac-0.11.7/sample-plugins/permissions/authz_policy.py $"

"""Permission policy enforcement through an authz-like configuration file.

Refer to SVN documentation for syntax of the authz file. Groups are supported.

As the fine-grained permissions brought by this permission policy are often
used in complement of the other pemission policies (like the
DefaultPermissionPolicy), there's no need to redefine all the permissions
here. Only additional rights or restrictions should be added.

Installation
------------

Note that this plugin requires the `configobj` package:

    http://www.voidspace.org.uk/python/configobj.html
    
You should be able to install it by doing a simple `easy_install configobj`


Enabling this policy requires listing it in the trac.ini:

[trac]
permission_policies = AuthzPolicy, DefaultPermissionPolicy

[authz_policy]
authz_file = conf/authzpolicy.conf


This means that the AuthzPolicy permissions will be checked first, and only
if no rule is found will the DefaultPermissionPolicy be used.


Configuration
-------------

The authzpolicy.conf file is a .ini style configuration file.

 - Each section of the config is a glob pattern used to match against a Trac
   resource descriptor. These descriptors are in the form:

     <realm>:<id>@<version>[/<realm>:<id>@<version> ...]

   Resources are ordered left to right, from parent to child.
   If any component is inapplicable, * is substituted.
   If the version pattern is not specified explicitely, all versions (@*)
   is added implicitly

   e.g. the WikiStart page will be matched by:
   
     [wiki:*]
     [wiki:WikiStart*]
     [wiki:WikiStart@*]
     [wiki:WikiStart]

   e.g. An attachment on WikiStart:

     wiki:WikiStart@117/attachment/FOO.JPG@*

   any of the following sections would match it:

     [wiki:*]
     [wiki:WikiStart*]
     [wiki:WikiStart@*]
     [wiki:WikiStart@*/attachment/*]
     [wiki:WikiStart@117/attachment/FOO.JPG]

 - Sections are checked against the current Trac resource **IN ORDER** of
   appearance in the configuration file. ORDER IS CRITICAL.

 - Once a section matches, the current username is matched, **IN ORDER**,
   against the keys of the section. If a key is prefixed with a @, it is
   treated as a group. If a key is prefixed with a !, the permission is denied
   rather than granted. The username will match any of 'anonymous',
   'authenticated', <username> or '*', using normal Trac permission rules.

Example configuration:

    [groups]
    administrators = athomas

    [*/attachment:*]
    * = WIKI_VIEW, TICKET_VIEW

    [wiki:WikiStart@*]
    @administrators = WIKI_ADMIN
    anonymous = WIKI_VIEW
    * = WIKI_VIEW

    # Deny access to page templates
    [wiki:PageTemplates/*]
    * =

    # Match everything else
    [*]
    @administrators = TRAC_ADMIN
    anonymous = BROWSER_VIEW, CHANGESET_VIEW, FILE_VIEW, LOG_VIEW, MILESTONE_VIEW, POLL_VIEW, REPORT_SQL_VIEW, REPORT_VIEW, ROADMAP_VIEW, SEARCH_VIEW, TICKET_CREATE, TICKET_MODIFY, TICKET_VIEW, TIMELINE_VIEW, WIKI_CREATE, WIKI_MODIFY, WIKI_VIEW
    # Give authenticated users some extra permissions
    authenticated = REPO_SEARCH, XML_RPC


"""

import os
from fnmatch import fnmatch
from trac.core import *
from trac.config import Option
from trac.util.compat import set, groupby
from trac.perm import PermissionSystem, IPermissionPolicy
from configobj import ConfigObj


class AuthzPolicy(Component):

    implements(IPermissionPolicy)

    authz_file = Option('authz_policy', 'authz_file', None,
                        'Location of authz policy configuration file.')

    authz = None
    authz_mtime = None

    # IPermissionPolicy methods
    
    def check_permission(self, action, username, resource, perm):
        if self.authz_file and not self.authz_mtime or \
                os.path.getmtime(self.get_authz_file()) > self.authz_mtime:
            self.parse_authz()
        resource_key = self.normalise_resource(resource)
        self.log.debug('Checking %s on %s', action, resource_key)
        permissions = self.authz_permissions(resource_key, username)
        if permissions is None:
            return None                 # no match, can't decide
        elif permissions == ['']:
            return False                # all actions are denied

        # FIXME: expand all permissions once for all
        ps = PermissionSystem(self.env)
        for deny, perms in groupby(permissions,
                                    key=lambda p: p.startswith('!')):
            if deny and action in ps.expand_actions([p[1:] for p in perms]):
                return False            # action is explicitly denied
            elif action in ps.expand_actions(perms):
                return True            # action is explicitly granted

        return None                    # no match for action, can't decide

    # Internal methods

    def get_authz_file(self):
        f = self.authz_file
        return os.path.isabs(f) and f or os.path.join(self.env.path, f)

    def parse_authz(self):
        self.env.log.debug('Parsing authz security policy %s' %
                           self.get_authz_file())
        self.authz = ConfigObj(self.get_authz_file())
        self.groups_by_user = {}
        for group, users in self.authz.get('groups', {}).iteritems():
            if isinstance(users, basestring):
                users = [users]
            for user in users:
                self.groups_by_user.setdefault(user, set()).add('@' + group)
        self.authz_mtime = os.path.getmtime(self.get_authz_file())

    def normalise_resource(self, resource):
        def flatten(resource):
            if not resource or not (resource.realm or resource.id):
                return []
            # XXX Due to the mixed functionality in resource we can end up with
            # ticket, ticket:1, ticket:1@10. This code naively collapses all
            # subsets of the parent resource into one. eg. ticket:1@10
            parent = resource.parent
            while parent and (resource.realm == parent.realm or \
                    (resource.realm == parent.realm and resource.id == parent.id)):
                parent = parent.parent
            if parent:
                parent = flatten(parent)
            else:
                parent = []
            return parent + ['%s:%s@%s' % (resource.realm or '*',
                                           resource.id or '*',
                                           resource.version or '*')]
        return '/'.join(flatten(resource))

    def authz_permissions(self, resource_key, username):
        # TODO: Handle permission negation in sections. eg. "if in this
        # ticket, remove TICKET_MODIFY"
        valid_users = ['*', 'anonymous']
        if username and username != 'anonymous':
            valid_users += ['authenticated', username]
        for resource_section in [a for a in self.authz.sections
                                 if a != 'groups']:
            resource_glob = resource_section
            if '@' not in resource_glob:
                resource_glob += '@*'

            if fnmatch(resource_key, resource_glob):
                section = self.authz[resource_section]
                for who, permissions in section.iteritems():
                    if who in valid_users or \
                            who in self.groups_by_user.get(username, []):
                        self.env.log.debug('%s matched section %s for user %s'
                                % (resource_key, resource_glob, username))
                        if isinstance(permissions, basestring):
                            return [permissions]
                        else:
                            return permissions
        return None
