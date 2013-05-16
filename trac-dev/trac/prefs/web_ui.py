## -*- coding: utf-8 -*-
##
## Copyright (C) 2004-2009 Edgewall Software
## Copyright (C) 2004-2005 Daniel Lundin <daniel@edgewall.com>
## All rights reserved.
##
## This software is licensed as described in the file COPYING, which
## you should have received as part of this distribution. The terms
## are also available at http://trac.edgewall.org/wiki/TracLicense.
##
## This software consists of voluntary contributions made by many
## individuals. For the exact contribution history, see the revision
## history and logs, available at http://trac.edgewall.org/log/.
##
## Author: Daniel Lundin <daniel@edgewall.com>
#
#from datetime import datetime
#import pkg_resources
#import re
#
#from genshi.builder import tag
#
#from trac.core import *
#from trac.prefs.api import IPreferencePanelProvider
#from trac.util.datefmt import all_timezones, get_timezone, localtz
#from trac.util.translation import _
#from trac.web import HTTPNotFound, IRequestHandler
#from trac.web.chrome import add_notice, add_stylesheet, \
#                            INavigationContributor, ITemplateProvider
#
#
#class PreferencesModule(Component):
#
#    panel_providers = ExtensionPoint(IPreferencePanelProvider)
#
#    implements(INavigationContributor, IPreferencePanelProvider,
#               IRequestHandler, ITemplateProvider)
#
#    _form_fields = ['newsid', 'name', 'email', 'tz', 'accesskeys']
#
#    # INavigationContributor methods
#
#    def get_active_navigation_item(self, req):
#        return 'prefs'
#
#    def get_navigation_items(self, req):
#        yield ('metanav', 'prefs',
#               tag.a(_('Preferences'), href=req.href.prefs()))
#
#    # IRequestHandler methods
#
#    def match_request(self, req):
#        match = re.match('/prefs(?:/([^/]+))?$', req.path_info)
#        if match:
#            req.args['panel_id'] = match.group(1)
#            return True
#
#    def process_request(self, req):
#        panel_id = req.args['panel_id']
#
#        panels = []
#        chosen_provider = None
#
#        for provider in self.panel_providers:
#            for name, label in provider.get_preference_panels(req):
#                if name == panel_id or None:
#                    chosen_provider = provider
#                panels.append((name, label))
#        if not chosen_provider:
#            self.log.warn('Unknown preference panel %r', panel_id)
#            raise HTTPNotFound(_('Unknown preference panel'))
#
#        template, data = chosen_provider.render_preference_panel(req, panel_id)
#        data.update({'active_panel': panel_id, 'panels': panels})
#
#        add_stylesheet(req, 'common/css/prefs.css')
#        return template, data, None
#
#    # IPreferencePanelProvider methods
#
#    def get_preference_panels(self, req):
#        yield (None, _('General'))
#        yield ('datetime', _('Date & Time'))
#        yield ('keybindings', _('Keyboard Shortcuts'))
#        if not req.authname or req.authname == 'anonymous':
#            yield ('advanced', _('Advanced'))
#
#    def render_preference_panel(self, req, panel):
#        if req.method == 'POST':
#            if 'restore' in req.args:
#                self._do_load(req)
#            else:
#                self._do_save(req)
#            req.redirect(req.href.prefs(panel or None))
#
#        return 'prefs_%s.html' % (panel or 'general'), {
#            'settings': {'session': req.session, 'session_id': req.session.sid},
#            'timezones': all_timezones, 'timezone': get_timezone,
#            'localtz': localtz
#        }
#
#    # ITemplateProvider methods
#
#    def get_htdocs_dirs(self):
#        return []
#
#    def get_templates_dirs(self):
#        return [pkg_resources.resource_filename('trac.prefs', 'templates')]
#
#    # Internal methods
#
#    def _do_save(self, req):
#        for field in self._form_fields:
#            val = req.args.get(field)
#            if val:
#                if field == 'tz' and 'tz' in req.session and \
#                        val not in all_timezones:
#                    del req.session['tz']
#                elif field == 'newsid' and val:
#                    req.session.change_sid(val)
#                elif field == 'accesskeys' and val:
#                    req.session[field] = '1'
#                else:
#                    req.session[field] = val
#            elif field in req.session and (field in req.args or
#                                           field + '_cb' in req.args):
#                del req.session[field]
#        add_notice(req, _('Your preferences have been saved.'))
#
#    def _do_load(self, req):
#        if req.authname == 'anonymous':
#            oldsid = req.args.get('loadsid')
#            req.session.get_session(oldsid)
