# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
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
#         Christopher Lenz <cmlenz@gmx.de>

import time
from datetime import datetime

from trac.core import *
from trac.resource import Resource
from trac.util.datefmt import utc, to_timestamp
from trac.util.translation import _
from trac.wiki.api import WikiSystem


class WikiPage(object):
    """Represents a wiki page (new or existing)."""

    realm = 'wiki'

    def __init__(self, env, name=None, version=None, db=None):
        self.env = env
        if isinstance(name, Resource):
            self.resource = name
            name = self.resource.id
        else:
            self.resource = Resource('wiki', name, version)
        self.name = name
        if name:
            self._fetch(name, version, db)
        else:
            self.version = 0
            self.text = ''
            self.readonly = 0
        self.old_text = self.text
        self.old_readonly = self.readonly

    def _fetch(self, name, version=None, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        if version:
            cursor.execute("SELECT version,time,author,text,comment,readonly "
                           "FROM wiki "
                           "WHERE name=%s AND version=%s",
                           (name, int(version)))
        else:
            cursor.execute("SELECT version,time,author,text,comment,readonly "
                           "FROM wiki "
                           "WHERE name=%s ORDER BY version DESC LIMIT 1",
                           (name,))
        row = cursor.fetchone()
        if row:
            version,time,author,text,comment,readonly = row
            self.version = int(version)
            self.author = author
            self.time = datetime.fromtimestamp(time, utc)
            self.text = text
            self.comment = comment
            self.readonly = readonly and int(readonly) or 0
        else:
            self.version = 0
            self.text = self.comment = self.author = ''
            self.time = None
            self.readonly = 0

    exists = property(fget=lambda self: self.version > 0)

    def delete(self, version=None, db=None):
        assert self.exists, 'Cannot delete non-existent page'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        if version is None:
            # Delete a wiki page completely
            cursor.execute("DELETE FROM wiki WHERE name=%s", (self.name,))
            self.env.log.info('Deleted page %s' % self.name)
        else:
            # Delete only a specific page version
            cursor.execute("DELETE FROM wiki WHERE name=%s and version=%s",
                           (self.name, version))
            self.env.log.info('Deleted version %d of page %s'
                              % (version, self.name))

        if version is None or version == self.version:
            self._fetch(self.name, None, db)

        if not self.exists:
            from trac.attachment import Attachment
            # Delete orphaned attachments
            Attachment.delete_all(self.env, 'wiki', self.name, db)

        if handle_ta:
            db.commit()

        # Let change listeners know about the deletion
        if not self.exists:
            for listener in WikiSystem(self.env).change_listeners:
                listener.wiki_page_deleted(self)
        else:
            for listener in WikiSystem(self.env).change_listeners:
                if hasattr(listener, 'wiki_page_version_deleted'):
                    listener.wiki_page_version_deleted(self)


    def save(self, author, comment, remote_addr, t=None, db=None):
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        if t is None:
            t = datetime.now(utc)

        if self.text != self.old_text:
            cursor = db.cursor()
            cursor.execute("INSERT INTO wiki (name,version,time,author,ipnr,"
                           "text,comment,readonly) VALUES (%s,%s,%s,%s,%s,%s,"
                           "%s,%s)", (self.name, self.version + 1,
                                      to_timestamp(t), author, remote_addr,
                                      self.text, comment, self.readonly))
            self.version += 1
            self.resource = self.resource(version=self.version)
        elif self.readonly != self.old_readonly:
            cursor = db.cursor()
            cursor.execute("UPDATE wiki SET readonly=%s WHERE name=%s",
                           (self.readonly, self.name))
        else:
            raise TracError(_('Page not modified'))

        if handle_ta:
            db.commit()

        for listener in WikiSystem(self.env).change_listeners:
            if self.version == 1:
                listener.wiki_page_added(self)
            else:
                listener.wiki_page_changed(self, self.version, t, comment,
                                           author, remote_addr)

        self.old_readonly = self.readonly
        self.old_text = self.text

    def get_history(self, db=None):
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT version,time,author,comment,ipnr FROM wiki "
                       "WHERE name=%s AND version<=%s "
                       "ORDER BY version DESC", (self.name, self.version))
        for version,ts,author,comment,ipnr in cursor:
            time = datetime.fromtimestamp(ts, utc)
            yield version,time,author,comment,ipnr
