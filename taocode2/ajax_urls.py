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


from taocode2.helper.utils import *
from taocode2.helper.validator import fast_validator,fclean
from taocode2.apps.project.forms import NewProjectForm
from taocode2.apps.user.forms import NewUserForm

__fvs = {}
fast_validator(__fvs, SITE_ROOT + '/ajax/prj/clean', NewProjectForm)
fast_validator(__fvs, SITE_ROOT + '/ajax/user/clean', NewUserForm)

@as_json
def user_fclean(request, fid):
    return fclean(request, __fvs, fid)

@as_json
def prj_fclean(request, fid):
    return fclean(request, __fvs, fid)


u = ['',
     (r'^msg/unread_count/$', 'apps.message.views.get_unread_count'),
     (r'^msg/send/$', 'apps.message.views.send_msg'),
     (r'^msg/move/$', 'apps.message.views.move_msg'),
     (r'^msg/del/$', 'apps.message.views.del_msg'),
     
     (r'^prj/watch/(?P<name>[-\w]+)/$',    'apps.project.views.watch_project'),
     (r'^prj/clean/(?P<fid>[\w]+)/$',    'ajax_urls.prj_fclean'), 
     (r'^prj/invite/(?P<name>[-\w]+)/$', 'apps.project.admin.do_invite'), 
     (r'^prj/del_member/(?P<name>[-\w]+)/$', 'apps.project.admin.del_member'), 
     (r'^prj/accept/(?P<name>[-\w]+)/$', 'apps.project.admin.do_accept'), 
     (r'^prj/reject/(?P<name>[-\w]+)/$', 'apps.project.admin.do_reject'), 
     (r'^prj/exit/(?P<name>[-\w]+)/$', 'apps.project.admin.do_exit'), 
     (r'^prj/members/(?P<name>[-\w]+)/$', 'apps.project.admin.get_members'), 

     (r'^prj/del/(?P<name>[-\w]+)/$', 'apps.project.admin.del_prj'), 
     (r'^prj/edit/(?P<name>[-\w]+)/$', 'apps.project.admin.edit_prj'), 

     (r'^issue/del/$', 'apps.issue.admin.del_issue'),
     (r'^issue/tags/(?P<name>[-\w]+)/$',    'apps.issue.props.get_tags'),
     (r'^issue/new_tag/(?P<name>[-\w]+)/$',    'apps.issue.props.new_tag'),
     (r'^issue/del_tag/(?P<name>[-\w]+)/$',    'apps.issue.props.del_tag'),

     (r'^issue/new_comment/(?P<issue_id>\d+)/$', 'apps.issue.comments.new_comment'),
     (r'^issue/comments/(?P<issue_id>\d+)/$',    'apps.issue.comments.get_comments'),
     (r'^issue/del_comment/$',    'apps.issue.comments.del_comment'),

     (r'^user/clean/(?P<fid>[\w]+)/$',    'ajax_urls.user_fclean'), 
     (r'^user/edit_my/$',    'apps.user.views.do_edit_my'), 
     (r'^user/edit_email/$',    'apps.user.views.do_edit_email'), 
     (r'^user/watch/(?P<name>[-\w]+)/$',    'apps.user.views.watch_user'),

     (r'^user/checkname/(?P<name>[-\w]+)/$',    'apps.user.views.check_name'),
     (r'^user/checkemail/(?P<email>[-\w|@|.]+)/$',    'apps.user.views.check_email'),
     (r'^user/checkemailauth/$',    'apps.user.views.check_email_auth'),
     (r'^user/checknameauth/$',    'apps.user.views.check_name_auth'),

     (r'^delfile/$', 'apps.main.files.del_file'),

     ]

urlpatterns = patterns(*u)
