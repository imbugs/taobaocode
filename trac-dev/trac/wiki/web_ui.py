# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2004-2005 Christopher Lenz <cmlenz@gmx.de>
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

from datetime import datetime
import pkg_resources
import re

from genshi.core import Markup
from genshi.builder import tag

from trac.attachment import AttachmentModule
from trac.config import IntOption,CONTEXT_PATH
from trac.core import *
from trac.mimeview.api import Mimeview, IContentConverter, Context
from trac.perm import IPermissionRequestor
from trac.resource import *
from trac.search import ISearchSource, search_to_sql, shorten_result
from trac.timeline.api import ITimelineEventProvider
from trac.util import get_reporter_id
from trac.util.datefmt import to_timestamp, utc
from trac.util.text import shorten_line
from trac.util.translation import _
from trac.versioncontrol.diff import get_diff_options, diff_blocks
from trac.web.chrome import add_ctxtnav, add_link, add_notice, add_script, \
                            add_stylesheet, add_warning, prevnext_nav, \
                            INavigationContributor, ITemplateProvider
from trac.web import IRequestHandler
from trac.wiki.api import IWikiPageManipulator, WikiSystem
from trac.wiki.formatter import format_to
from trac.wiki.model import WikiPage


class HomeModule(Component):
    implements(INavigationContributor)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'home'

    def get_navigation_items(self, req):
        yield ('mainnav', 'home',
            tag.a(_('Home'), href=CONTEXT_PATH+"/project"+req.href.projectHome(),title=_('Home'),accesskey=0))
        
class InvalidWikiPage(TracError):
    """Exception raised when a Wiki page fails validation.
    
    :deprecated: Not used anymore since 0.11
    """
 

class WikiModule(Component):

    implements(IContentConverter, INavigationContributor, IPermissionRequestor,
               IRequestHandler, ITimelineEventProvider, ISearchSource,
               ITemplateProvider)

    page_manipulators = ExtensionPoint(IWikiPageManipulator)

    max_size = IntOption('wiki', 'max_size', 2097152,
        """Maximum allowed wiki page size in bytes. (''since 0.11.2'')""")

    PAGE_TEMPLATES_PREFIX = 'PageTemplates/'
    DEFAULT_PAGE_TEMPLATE = 'DefaultPage'

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('txt', _('Plain Text'), 'txt', 'text/x-trac-wiki', 'text/plain',
               9)

    def convert_content(self, req, mimetype, content, key):
        # Tell the browser that the content should be downloaded and
        # not rendered. The x=y part is needed to keep Safari from being 
        # confused by the multiple content-disposition headers.
        req.send_header('Content-Disposition', 'attachment; x=y')

        return (content, 'text/plain;charset=utf-8')

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'wiki'

    def get_navigation_items(self, req):
        if 'WIKI_VIEW' in req.perm('wiki'):
            yield ('mainnav', 'wiki',
                   tag.a(_('Wiki'), href=req.href.wiki(), accesskey=1))
            yield ('metanav', 'help',
                   tag.a(_('Help/Guide'), href=req.href.wiki('TracGuide'),
                         accesskey=6))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['WIKI_CREATE', 'WIKI_DELETE', 'WIKI_MODIFY', 'WIKI_VIEW']
        return actions + [('WIKI_ADMIN', actions)]

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/wiki(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return 1

    def process_request(self, req):
        action = req.args.get('action', 'view')
        pagename = req.args.get('page', 'WikiStart')
        version = req.args.get('version')
        old_version = req.args.get('old_version')

        if pagename.endswith('/'):
            req.redirect(req.href.wiki(pagename.strip('/')))

        page = WikiPage(self.env, pagename)
        versioned_page = WikiPage(self.env, pagename, version=version)

        req.perm(page.resource).require('WIKI_VIEW')
        req.perm(versioned_page.resource).require('WIKI_VIEW')

        if version and versioned_page.version == 0 and \
               page.version != 0:
            raise TracError(_('No version "%(num)s" for Wiki page "%(name)s"',
                              num=version, name=page.name))

        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'common/css/code_ext.css')

        if req.method == 'POST':
            if action == 'edit':
                if 'cancel' in req.args:
                    req.redirect(req.href.wiki(page.name))
                
                has_collision = int(version) != page.version
                for a in ('preview', 'diff', 'merge'):
                    if a in req.args:
                        action = a
                        break
                valid = self._validate(req, versioned_page)
                if action == 'edit' and not has_collision and valid:
                    return self._do_save(req, versioned_page)
                else:
                    return self._render_editor(req, page, action, has_collision)
            elif action == 'delete':
                self._do_delete(req, versioned_page)
            elif action == 'diff':
                get_diff_options(req)
                req.redirect(req.href.wiki(versioned_page.name, action='diff',
                                           old_version=old_version))
        elif action == 'delete':
            return self._render_confirm(req, versioned_page)
        elif action == 'edit':
            return self._render_editor(req, versioned_page)
        elif action == 'diff':
            return self._render_diff(req, versioned_page)
        elif action == 'history':
            return self._render_history(req, versioned_page)
        else:
            format = req.args.get('format')
            if format:
                Mimeview(self.env).send_converted(req, 'text/x-trac-wiki',
                                                  versioned_page.text,
                                                  format, versioned_page.name)
            return self._render_view(req, versioned_page)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('trac.wiki', 'templates')]

    # Internal methods

    def _validate(self, req, page):
        valid = True
        
        # Validate page size
        if len(req.args.get('text', '')) > self.max_size:
            add_warning(req, _('The wiki page is too long (must be less '
                               'than %(num)s characters)',
                               num=self.max_size))
            valid = False

        # Give the manipulators a pass at post-processing the page
        for manipulator in self.page_manipulators:
            for field, message in manipulator.validate_wiki_page(req, page):
                valid = False
                if field:
                    add_warning(req, _("The Wiki page field '%(field)s' is "
                                       "invalid: %(message)s",
                                       field=field, message=message))
                else:
                    add_warning(req, _("Invalid Wiki page: %(message)s",
                                       message=message))
        return valid

    def _page_data(self, req, page, action=''):
        title = get_resource_summary(self.env, page.resource)
        if action:
            title += ' (%s)' % action
        return {'page': page, 'action': action, 'title': title}

    def _prepare_diff(self, req, page, old_text, new_text,
                      old_version, new_version):
        diff_style, diff_options, diff_data = get_diff_options(req)
        diff_context = 3
        for option in diff_options:
            if option.startswith('-U'):
                diff_context = int(option[2:])
                break
        if diff_context < 0:
            diff_context = None
        diffs = diff_blocks(old_text, new_text, context=diff_context,
                            ignore_blank_lines='-B' in diff_options,
                            ignore_case='-i' in diff_options,
                            ignore_space_changes='-b' in diff_options)
        def version_info(v, last=0):
            return {'path': get_resource_name(self.env, page.resource),
                    'rev': v or 'currently edited', 
                    'shortrev': v or last + 1,
                    'href': v and req.href.wiki(page.name, version=v) or None}
        changes = [{'diffs': diffs, 'props': [],
                    'new': version_info(new_version, old_version),
                    'old': version_info(old_version)}]

        add_stylesheet(req, 'common/css/diff.css')
        add_script(req, 'common/js/diff.js')
        return diff_data, changes

    def _do_delete(self, req, page):
        if page.readonly:
            req.perm(page.resource).require('WIKI_ADMIN')
        else:
            req.perm(page.resource).require('WIKI_DELETE')

        if 'cancel' in req.args:
            req.redirect(get_resource_url(self.env, page.resource, req.href))

        version = int(req.args.get('version', 0)) or None
        old_version = int(req.args.get('old_version', 0)) or version

        db = self.env.get_db_cnx()
        if version and old_version and version > old_version:
            # delete from `old_version` exclusive to `version` inclusive:
            for v in range(old_version, version):
                page.delete(v + 1, db)
        else:
            # only delete that `version`, or the whole page if `None`
            page.delete(version, db)
        db.commit()

        if not page.exists:
            add_notice(req, _('The page %(name)s has been deleted.',
                              name=page.name))
            req.redirect(req.href.wiki())
        else:
            if version and old_version and version > old_version + 1:
                add_notice(req, _('The versions %(from_)d to %(to)d of the '
                                  'page %(name)s have been deleted.',
                            from_=old_version + 1, to=version, name=page.name))
            else:
                add_notice(req, _('The version %(version)d of the page '
                                  '%(name)s has been deleted.',
                                  version=version, name=page.name))
            req.redirect(req.href.wiki(page.name))

    def _do_save(self, req, page):
        if page.readonly:
            req.perm(page.resource).require('WIKI_ADMIN')
        elif not page.exists:
            req.perm(page.resource).require('WIKI_CREATE')
        else:
            req.perm(page.resource).require('WIKI_MODIFY')

        page.text = req.args.get('text')
        if 'WIKI_ADMIN' in req.perm(page.resource):
            # Modify the read-only flag if it has been changed and the user is
            # WIKI_ADMIN
            page.readonly = int('readonly' in req.args)

        try:
            page.save(get_reporter_id(req, 'author'),
                            req.args.get('comment'),
                            req.remote_addr)
            add_notice(req, _('Your changes have been saved.'))
            req.redirect(get_resource_url(self.env, page.resource, req.href,
                                          version=None))
        except TracError:
            add_warning(req, _("Page not modified, showing latest version."))
            return self._render_view(req, page)

    def _render_confirm(self, req, page):
        if page.readonly:
            req.perm(page.resource).require('WIKI_ADMIN')
        else:
            req.perm(page.resource).require('WIKI_DELETE')

        version = None
        if 'delete_version' in req.args:
            version = int(req.args.get('version', 0))
        old_version = int(req.args.get('old_version') or 0) or version

        data = self._page_data(req, page, 'delete')
        data.update({'new_version': None, 'old_version': None,
                     'num_versions': 0})
        if version is not None:
            num_versions = 0
            for v,t,author,comment,ipnr in page.get_history():
                num_versions += 1;
                if num_versions > 1:
                    break
            data.update({'new_version': version, 'old_version': old_version,
                         'num_versions': num_versions})
        self._wiki_ctxtnav(req, page)
        return 'wiki_delete.html', data, None

    def _render_diff(self, req, page):
        if not page.exists:
            raise TracError(_('Version %(num)s of page "%(name)s" does not '
                              'exist',
                              num=req.args.get('version'), name=page.name))

        old_version = req.args.get('old_version')
        if old_version:
            old_version = int(old_version)
            if old_version == page.version:
                old_version = None
            elif old_version > page.version:
                # FIXME: what about reverse diffs?
                old_version = page.resource.version
                page = WikiPage(self.env, page.name, version=old_version)
                req.perm(page.resource).require('WIKI_VIEW')
        latest_page = WikiPage(self.env, page.name, version=None)
        req.perm(latest_page.resource).require('WIKI_VIEW')
        new_version = int(page.version)

        date = author = comment = ipnr = None
        num_changes = 0
        old_page = None
        prev_version = next_version = None
        for version, t, a, c, i in latest_page.get_history():
            if version == new_version:
                date = t
                author = a or 'anonymous'
                comment = c or '--'
                ipnr = i or ''
            else:
                if version < new_version:
                    num_changes += 1
                    if not prev_version:
                        prev_version = version
                    if (old_version and version == old_version) or \
                            not old_version:
                        old_version = version
                        old_page = WikiPage(self.env, page.name, old_version)
                        req.perm(old_page.resource).require('WIKI_VIEW')
                        break
                else:
                    next_version = version
        if not old_version:
            old_version = 0

        # -- text diffs
        old_text = old_page and old_page.text.splitlines() or []
        new_text = page.text.splitlines()
        diff_data, changes = self._prepare_diff(req, page, old_text, new_text,
                                                old_version, new_version)

        # -- prev/up/next links
        if prev_version:
            add_link(req, 'prev', req.href.wiki(page.name, action='diff',
                                                version=prev_version),
                     _('Version %(num)s', num=prev_version))
        add_link(req, 'up', req.href.wiki(page.name, action='history'),
                 _('Page history'))
        if next_version:
            add_link(req, 'next', req.href.wiki(page.name, action='diff',
                                                version=next_version),
                     _('Version %(num)s', num=next_version))

        data = self._page_data(req, page, 'diff')
        data.update({ 
            'change': {'date': date, 'author': author, 'ipnr': ipnr,
                       'comment': comment},
            'new_version': new_version, 'old_version': old_version,
            'latest_version': latest_page.version,
            'num_changes': num_changes,
            'longcol': 'Version', 'shortcol': 'v',
            'changes': changes,
            'diff': diff_data,
        })
        prevnext_nav(req, _('Change'), _('Wiki History'))
        return 'wiki_diff.html', data, None

    def _render_editor(self, req, page, action='edit', has_collision=False):
        if has_collision:
            if action == 'merge':
                page = WikiPage(self.env, page.name, version=None)
                req.perm(page.resource).require('WIKI_VIEW')
            else:
                action = 'collision'

        if page.readonly:
            req.perm(page.resource).require('WIKI_ADMIN')
        else:
            req.perm(page.resource).require('WIKI_MODIFY')
        original_text = page.text
        if 'text' in req.args:
            page.text = req.args.get('text')
        elif 'template' in req.args:
            template = self.PAGE_TEMPLATES_PREFIX + req.args.get('template')
            template_page = WikiPage(self.env, template)
            if template_page and template_page.exists and \
                   'WIKI_VIEW' in req.perm(template_page.resource):
                page.text = template_page.text
        if action == 'preview':
            page.readonly = 'readonly' in req.args

        author = get_reporter_id(req, 'author')
        comment = req.args.get('comment', '')
        editrows = req.args.get('editrows')
        
        if editrows:
            pref = req.session.get('wiki_editrows', '20')
            if editrows != pref:
                req.session['wiki_editrows'] = editrows
        else:
            editrows = req.session.get('wiki_editrows', '20')

        data = self._page_data(req, page, action)
        data.update({
            'author': author,
            'comment': comment,
            'edit_rows': editrows,
            'scroll_bar_pos': req.args.get('scroll_bar_pos', ''),
            'diff': None,
        })
        if action in ('diff', 'merge'):
            old_text = original_text and original_text.splitlines() or []
            new_text = page.text and page.text.splitlines() or []
            diff_data, changes = self._prepare_diff(
                req, page, old_text, new_text, page.version, '')
            data.update({'diff': diff_data, 'changes': changes,
                         'action': 'preview', 'merge': action == 'merge',
                         'longcol': 'Version', 'shortcol': 'v'})
        
        self._wiki_ctxtnav(req, page)
        return 'wiki_edit.html', data, None

    def _render_history(self, req, page):
        """Extract the complete history for a given page.

        This information is used to present a changelog/history for a given
        page.
        """
        if not page.exists:
            raise TracError(_("Page %(name)s does not exist", name=page.name))

        data = self._page_data(req, page, 'history')

        history = []
        for version, date, author, comment, ipnr in page.get_history():
            history.append({
                'version': version,
                'date': date,
                'author': author,
                'comment': comment,
                'ipnr': ipnr
            })
        data.update({'history': history, 'resource': page.resource})
        add_ctxtnav(req, 'Back to '+page.name, req.href.wiki(page.name))
        return 'history_view.html', data, None

    def _render_view(self, req, page):
        version = page.resource.version

        # Add registered converters
        if page.exists:
            for conversion in Mimeview(self.env).get_supported_conversions(
                                                 'text/x-trac-wiki'):
                conversion_href = req.href.wiki(page.name, version=version,
                                                format=conversion[0])
                # or...
                conversion_href = get_resource_url(self.env, page.resource,
                                                req.href, format=conversion[0])
                add_link(req, 'alternate', conversion_href, conversion[1],
                         conversion[3])

        data = self._page_data(req, page)
        if page.name == 'WikiStart':
            data['title'] = ''

        if not page.exists:
            if 'WIKI_CREATE' not in req.perm(page.resource):
                raise ResourceNotFound(_('Page %(name)s not found',
                                         name=page.name))

        latest_page = WikiPage(self.env, page.name, version=None)
        req.perm(latest_page.resource).require('WIKI_VIEW')

        prev_version = next_version = None
        if version:
            try:
                version = int(version)
                for hist in latest_page.get_history():
                    v = hist[0]
                    if v != version:
                        if v < version:
                            if not prev_version:
                                prev_version = v
                                break
                        else:
                            next_version = v
            except ValueError:
                version = None
            
        prefix = self.PAGE_TEMPLATES_PREFIX
        templates = [template[len(prefix):] for template in
                     WikiSystem(self.env).get_pages(prefix) if
                     'WIKI_VIEW' in req.perm('wiki', template)]

        # -- prev/up/next links
        if prev_version:
            add_link(req, 'prev',
                     req.href.wiki(page.name, version=prev_version),
                     _('Version %(num)s', num=prev_version))

        parent = None
        if version:
            add_link(req, 'up', req.href.wiki(page.name, version=None),
                     _('View latest version'))
        elif '/' in page.name:
            parent = page.name[:page.name.rindex('/')]
            add_link(req, 'up', req.href.wiki(parent, version=None),
                     _("View parent page"))
        
        if next_version:
            add_link(req, 'next',
                     req.href.wiki(page.name, version=next_version),
                     _('Version %(num)s', num=next_version))

        # Add ctxtnav entries
        if version:
            prevnext_nav(req, _('Version'), _('View Latest Version'))
            add_ctxtnav(req, _('Last Change'),
                        req.href.wiki(page.name, action='diff',
                                      version=page.version))
        else:
            if parent:
                add_ctxtnav(req, _('Up'), req.href.wiki(parent))
            self._wiki_ctxtnav(req, page)

        context = Context.from_request(req, page.resource)
        data.update({
            'context': context,
            'latest_version': latest_page.version,
            'attachments': AttachmentModule(self.env).attachment_data(context),
            'default_template': self.DEFAULT_PAGE_TEMPLATE,
            'templates': templates,
            'version': version
        })
        return 'wiki_view.html', data, None
    
    def _wiki_ctxtnav(self, req, page):
        """Add the normal wiki ctxtnav entries."""
        add_ctxtnav(req, _('Start Page'), req.href.wiki('WikiStart'))
        add_ctxtnav(req, _('Index'), req.href.wiki('TitleIndex'))
        if page.exists:
            add_ctxtnav(req, _('History'), req.href.wiki(page.name, 
                                                         action='history'))
            add_ctxtnav(req, _('Last Change'),
                        req.href.wiki(page.name, action='diff',
                                      version=page.version))

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'WIKI_VIEW' in req.perm:
            yield ('wiki', _('Wiki changes'))

    def get_timeline_events(self, req, start, stop, filters):
        db = self.env.get_db_cnx()
        if 'wiki' in filters:
            wiki_realm = Resource('wiki')
            cursor = db.cursor()
            cursor.execute("SELECT time,name,comment,author,version "
                           "FROM wiki WHERE time>=%s AND time<=%s",
                           (to_timestamp(start), to_timestamp(stop)))
            for ts,name,comment,author,version in cursor:
                wiki_page = wiki_realm(id=name, version=version)
                if 'WIKI_VIEW' not in req.perm(wiki_page):
                    continue
                yield ('wiki', datetime.fromtimestamp(ts, utc), author,
                       (wiki_page, comment))

            # Attachments
            for event in AttachmentModule(self.env).get_timeline_events(
                req, wiki_realm, start, stop):
                yield event

    def render_timeline_event(self, context, field, event):
        wiki_page, comment = event[3]
        if field == 'url':
            return context.href.wiki(wiki_page.id, version=wiki_page.version)
        elif field == 'title':
            return tag(tag.em(get_resource_name(self.env, wiki_page)),
                       wiki_page.version > 1 and ' edited' or ' created')
        elif field == 'description':
            markup = format_to(self.env, None, context(resource=wiki_page),
                               comment)
            if wiki_page.version > 1:
                diff_href = context.href.wiki(
                    wiki_page.id, version=wiki_page.version, action='diff')
                markup = tag(markup, ' ', tag.a('(diff)', href=diff_href))
            return markup

    # ISearchSource methods

    def get_search_filters(self, req):
        if 'WIKI_VIEW' in req.perm:
            yield ('wiki', _('Wiki'))

    def get_search_results(self, req, terms, filters):
        if not 'wiki' in filters:
            return
        db = self.env.get_db_cnx()
        sql_query, args = search_to_sql(db, ['w1.name', 'w1.author', 'w1.text'],
                                        terms)
        cursor = db.cursor()
        cursor.execute("SELECT w1.name,w1.time,w1.author,w1.text "
                       "FROM wiki w1,"
                       "(SELECT name,max(version) AS ver "
                       "FROM wiki GROUP BY name) w2 "
                       "WHERE w1.version = w2.ver AND w1.name = w2.name "
                       "AND " + sql_query, args)

        wiki_realm = Resource('wiki')
        for name, ts, author, text in cursor:
            page = wiki_realm(id=name)
            if 'WIKI_VIEW' in req.perm(page):
                yield (get_resource_url(self.env, page, req.href),
                       '%s: %s' % (name, shorten_line(text)),
                       datetime.fromtimestamp(ts, utc), author,
                       shorten_result(text, terms))
        
        # Attachments
        for result in AttachmentModule(self.env).get_search_results(
            req, wiki_realm, terms):
            yield result
