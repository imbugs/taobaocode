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

u = ['',
     ('^$',       'apps.project.views.view_project'),
     ('^info/$',       'apps.project.views.project_info'),
     ('^admin/$', 'apps.project.admin.project_admin'),
     ('^admin/resources/$', 'apps.project.admin.project_resources'),
     ('^watch/$', 'apps.project.views.project_watch_list'),

     (r'^file/(?P<fid>[\d]+)/', 'apps.main.files.get_file'),

     ('^issues/$', 'apps.issue.views.all_issues'),
     ('^issues/(?P<pagenum>\d+)$', 'apps.issue.views.all_issues'),
     ('^issues/(?P<pagenum>\d+)/(?P<key>.*)$', 'apps.issue.views.all_issues'),

     ('^issues/(?P<status>\w+)/$', 'apps.issue.views.list_issues'),
     ('^issues/(?P<status>\w+)/(?P<pagenum>\d+)$', 'apps.issue.views.list_issues'),
     ('^issues/(?P<status>\w+)/(?P<pagenum>\d+)/(?P<key>.*)$', 'apps.issue.views.list_issues'),

     ('^issue/(?P<issue_id>\d+)/$', 'apps.issue.views.view_issue'),
     ('^issue/change/(?P<issue_id>\d+)/$', 'apps.issue.admin.change_issue'),

     ('^issue/new/$', 'apps.issue.views.new_issue'),
    
     ('^src/$',                         'apps.repos.views.browse'),
     ('^src/(?P<path>.*)$',            'apps.repos.views.browse'),
     ('^logs/(?P<path>.*)',             'apps.repos.views.logs'),
     ('^log/(?P<rev>\d+)/$',            'apps.repos.views.log'),
     ('^log/(?P<rev>\d+)/(?P<path>.*)', 'apps.repos.views.log'),
     ('^diff/(?P<revN>\d+)/(?P<path>.*)', 'apps.repos.views.diff'),
     ('^diff/(?P<revN>\d+):(?P<revM>\d+)/$', 'apps.repos.views.diff'),
     ('^diff/(?P<revN>\d+):(?P<revM>\d+)/(?P<path>.*)', 'apps.repos.views.diff'),


     ('^del_wiki/$', 'apps.wiki.views.del_wiki'),
     ('^edit_wiki/$', 'apps.wiki.views.edit_wiki'),
     ('^edit_wiki/(?P<path>.*)/$', 'apps.wiki.views.edit_wiki'),
     ('^wiki/$', 'apps.wiki.views.wiki_index'),
     ('^wiki/(?P<path>.*)/$', 'apps.wiki.views.wiki_content'),
     ('^wikis/$', 'apps.wiki.views.wiki_list'),
     ('^wiki_changes/(?P<path>.*)/$', 'apps.wiki.views.wiki_changes'),
     ('^raw_wiki/(?P<path>.*)/$', 'apps.wiki.views.raw_wiki'),
     ('^raw_log_wiki/(?P<logid>\d+)/$', 'apps.wiki.views.raw_log_wiki'),
     ('^diff_log_wiki/(?P<logid>\d+)/$', 'apps.wiki.views.diff_log_wiki'),
     ]

urlpatterns = patterns(*u)
