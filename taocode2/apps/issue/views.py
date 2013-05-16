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


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import *
from django.utils.html import escape
from django.db.models import Count

from taocode2.models import *
from taocode2.helper.utils import *

from taocode2.helper import consts
from taocode2.helper.page import build_page
from taocode2.settings import SITE_ROOT
from taocode2.apps.project.views import update_my_project_status, build_prj_nav_menu
from taocode2.apps.project.admin import can_access
from taocode2.apps.project import prj_key
from taocode2.apps.main.files import add_file

from taocode2.apps.user import activity
from django.db.models import Q

__author__ = 'luqi@taobao.com'


def all_issues(request, name, pagenum=1, key=None):
    return query_issues(request, name,
                        pagenum, key)

def list_issues(request, name, status, pagenum=1, key=None):
    st = None
    if status == 'opened':
        st = consts.ISSUE_OPEN
    elif status == 'closed':
        st = consts.ISSUE_CLOSED
        
    return query_issues(request, name,
                        pagenum, key,
                        st)

def query_issues(request, name, pagenum, key, st=None):

    rc = request.rc

    project = q_get(Project, name=name)
    rc.navmenus = build_prj_nav_menu(request, project, 'issues')

    rc.bodymenus = [{'uri':'issues/', 'text':'all'},
                    {'uri':'issues/opened/', 'text':'opened'},
                    {'uri':'issues/closed/', 'text':'closed'}]
    
    prefix = 'issues'

    if st == consts.ISSUE_OPEN:
        rc.pagename = "Opened issues"
        prefix += '/opened'
        rc.bodymenus[1]['choice'] = True
    elif st == consts.ISSUE_CLOSED:
        rc.pagename = "Closed issues"
        prefix += '/closed'
        rc.bodymenus[2]['choice'] = True
    else:
        rc.pagename = "All issues"
        rc.bodymenus[0]['choice'] = True        
    if request.method == 'POST':
        q = request.POST.get('q', None)
        return redirect(SITE_ROOT + '/p/%s/%s/1/%s'%(name, prefix, q))
    
    resp = can_access(project, request.user)
    if resp != None:
        return resp

    rc.project_name = name
    rc.project = project

    update_my_project_status(request,[rc.project])

    if project is None:
        return send_response(request, 
                             'project/notfound.html')
    pagenum = int(pagenum)

    if key is not None:
        q = Q(Q(project=project), Q(Q(title__icontains=key) | Q(content__icontains=key)))
    else:
        q = Q(project=project)

    if st is not None:
        q = q & Q(status = st)

    q = q & ~Q(status = consts.ISSUE_DELETED)
    key_text = key and key.encode('utf8') or ''

    build_page(rc, Issue, q,
               pagenum,
               '/p/{0}/{1}'.format(name, prefix),
               key_text,
               order=['-mtime'])

    for i in rc.page.object_list:
        if request.user in (project.owner, i.creator):
            i.can_op = True
        else:
            i.can_op = False

        i.comments_count = IssueComment.objects.filter(issue=i).count();

    rc.key_text = key_text
    return send_response(request, 
                         'issue/list.html')

def view_issue(request, name, issue_id):
    rc = request.rc
    rc.project = q_get(Project, name = name)

    resp = can_access(rc.project, request.user)
    if resp != None:
        return resp

    issue = q_get(Issue, pk = issue_id)

    if issue.status == consts.ISSUE_DELETED:
        raise Http404
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content is not None:
            comment = IssueComment()
            comment.issue = issue
            comment.owner = request.user
            comment.content = content
            comment.status = consts.COMMENT_ENABLE
    
            comment.save()
            activity.new_comment(issue.project, request.user, comment)
            
            return redirect(reverse('apps.issue.views.view_issue', 
                                    args=[name, issue.id]))
            
            
    rc.issue = issue
    rc.pagename = '#%s - %s'%(rc.issue.id, rc.issue.title)
    rc.navmenus = build_prj_nav_menu(request, rc.project, 'issues')

    rc.comments = q_gets(IssueComment, issue=rc.issue, 
                         status = consts.COMMENT_ENABLE).order_by('ctime')

    rc.files = q_gets(ProjectAttachment, project=rc.project,
                      ftype='issue', ftid=rc.issue.id,
                      status = consts.FILE_ENABLE)

    rc.issueowner = request.user in (rc.issue.creator,
                                     rc.project.owner)

    return send_response(request, 
                         'issue/view.html')

@login_required
def new_issue(request, name):
    rc = request.rc
    project = q_get(Project, name = name)
    
    resp = can_access(project, request.user)
    if resp != None:
        return resp

    rc.project = project
    rc.pagename = 'create issue'
    rc.navmenus = build_prj_nav_menu(request, rc.project, 'issues')

    if request.method != 'POST':
        return send_response(request, 
                         'issue/new.html')
    
    title = request.POST.get('title', '')
    content = request.POST.get('content', '')
    
    if len(title) <= 0:
        return send_response(request, 
                             'issue/new.html')
    
    if len(content) <= 0:
        return send_response(request, 
                             'issue/new.html')
    
    issue = Issue()
    issue.project = rc.project
    
    issue.creator = request.user

    issue.title = title
    issue.content = content
    issue.status = consts.ISSUE_OPEN
    issue.vote_count = 0
    
    issue.save()

    # add file
    atts = request.FILES.getlist('attachment')
    fc = 0
    for f in atts:
        if fc <= prj_key.get(project, prj_key.UPLOAD_LIMIT_COUNT, 5):
            add_file(request, project, 'issue', issue.id, f)
            fc += 1

    activity.new_issue(rc.project, request.user, issue)

    return redirect(reverse('apps.issue.views.view_issue', 
                            args=[name, issue.id]))
