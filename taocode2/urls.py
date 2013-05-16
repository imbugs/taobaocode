# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Taobao .Inc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://code.taobao.org/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://code.taobao.org/.

from django.conf.urls.defaults import patterns, include
from taocode2.settings import SITE_ROOT

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


u = ['',
     ('^$', 'apps.main.views.index'),
     (r'^project/view/(?P<pid>\d+)/$', 'apps.project.views.view_old'),
     (r'^project/(?P<pid>\d+)/viewSvn/$', 'apps.project.views.view_old_src'),

     (r'^trac/(?P<name>[\w]+)/wiki/(?P<path>.*)', 'apps.project.views.view_old_wiki'),
     
     (r'^admin/', include(admin.site.urls)),
     ('^about/$', 'apps.main.views.show_page', {'name':'about.html','pagename':'About Taocode'},),
     ('^about/privacy/$', 'apps.main.views.show_page', {'name':'privacy.html','pagename':'Privacy'}),
     ('^about/license/$', 'apps.main.views.show_page', {'name':'license.html','pagename':'License'}),
     ('^license.html$', 'apps.main.views.show_page', {'name':'license.html','pagename':'License'}),

     # static file
     #
     ('^css/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : '/home/code/code.taobao.org/taocode2/media/css'}),
     ('^js/(?P<path>.*)$',  'django.views.static.serve', {'document_root' : '/home/code/code.taobao.org/taocode2/media/js'}),
     ('^img/(?P<path>.*)$', 'django.views.static.serve', {'document_root' : '/home/code/code.taobao.org/taocode2/media/img'}),

     
     # user profilerr
     #
     ('^u/(?P<name>[\.\s\-\w]+)/$',  'apps.user.views.view_user'),
     ('^my/$',           'apps.user.views.view_user'),
     ('^my/edit/$',      'apps.user.views.edit_my'),   
     ('^my/notify/$',    'apps.user.views.edit_notify'),      
     ('^my/newpwd/$',    'apps.user.authviews.change_password'),
     
     #login
     #
     ('^register/$',     'apps.user.views.register'),
     (r'^login/$',  'apps.user.views.login_view'),
     (r'^logout/$',  'apps.user.views.logout_view'),

     #verify
     #
     ('^reset/$',  'apps.user.authviews.reset_password'),
     ('^reset/(?P<code>[\w]+)/$',  'apps.user.authviews.reset_password_code'),

     ('^verify/(?P<code>[\w]+)/$',  'apps.user.verify.check_code'),
     ('^verify/(?P<code>[\w]+)/cancel/$',  'apps.user.verify.do_check_code_cancel'),
     ('^verify/(?P<code>[\w]+)/ok/$',  'apps.user.verify.do_check_code_ok'),
 
     #message
     #
     ('^msg/$',      'apps.message.views.show_box'),
     ('^msg/(?P<name>[\w]+)/$',      'apps.message.views.show_box'),
     ('^msg/(?P<name>[\w]+)/(?P<pagenum>\d+)/$',  'apps.message.views.show_box'),
    
     # projects
     #
     ('^all/$',                   'apps.project.views.all_projects'),
     ('^all/(?P<pagenum>\d+)/$',  'apps.project.views.all_projects'),
     ('^all/(?P<pagenum>\d+)/(?P<key>.*)/$',  'apps.project.views.all_projects'),

     ('^hot/$',                   'apps.project.views.list_projects', {'pt':'hot'}),
     ('^newest/$',                'apps.project.views.list_projects', {'pt':'newest'}),
     ('^random/$',                'apps.project.views.list_projects', {'pt':'random'}),
     ('^watched/$',               'apps.project.views.list_projects', {'pt':'watched'}),
 
     ('^new/$',                   'apps.project.views.new_project'),

     #project url
     #
     (r'^p/(?P<name>[\.\s\-\w]+)/',   include('prj_urls')),  
     ('^wiki_formarts/$', 'apps.wiki.views.wiki_formarts'),

     #api
     #
     (r'^api/', include('api.urls')),         
     
     #ajax
     #
     (r'^ajax/', include('ajax_urls')),

     #opens
     (r'^open/', include('apps.open.urls')),

     ]

urlpatterns = patterns(*u)
