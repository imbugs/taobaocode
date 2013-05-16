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
from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper import consts
from taocode2.apps.user import activity

from django.core.urlresolvers import reverse
from django.http import *

__author__ = 'luqi@taobao.com'


def get_issue(request, issue_id):
    issue = q_get(Issue, pk=issue_id)
    if issue is None:
        return None

    if issue.status == consts.ISSUE_DELETED:
        return None

    if request.user not in (issue.project.owner, issue.creator):
        return None
    return issue

def update_status(request, issue_id, status):
    issue = get_issue(request, issue_id)
    if issue is None:
        return False

    issue.status = status
    issue.save()
    
    if status == consts.ISSUE_DELETED:
        activity.del_issue(issue.project, request.user, issue)
    elif status == consts.ISSUE_CLOSED:
        activity.close_issue(issue.project, request.user, issue)
    elif status == consts.ISSUE_OPEN:
        activity.reopen_issue(issue.project, request.user, issue)

    return True

@as_json
@login_required
def del_issue(request):
    if request.method != 'POST':
        return False
    issue_id = request.POST.get('issue_id')
    return update_status(request, issue_id,
                         consts.ISSUE_DELETED)
def close_issue(request, issue_id):
    if update_status(request, issue_id,
                     consts.ISSUE_CLOSED) is False:
        return False
    
    return (True, consts.ISSUE_CLOSED)

def reopen_issue(request, issue_id):
    if update_status(request, issue_id,
                     consts.ISSUE_OPEN) is False:
        return False

    return (True, consts.ISSUE_OPEN)

@as_json
@login_required
def edit_issue(request, issue_id):
    if request.method != 'POST':
        return False

    content = request.POST.get('c','').strip()
    if len(content) <= 0:
        return False

    title = request.POST.get('t','').strip()
    if len(title) <= 0:
        return False
    
    issue = get_issue(request, issue_id)
    if issue is None:
        return False

    issue.title = title
    issue.content = content
    issue.save()

    activity.edit_issue(issue.project, request.user, issue)

    return (True, content)

@as_json
@login_required
def del_issue_file(request, file_id):
    issuefile = q_get(IssueAttachment, pk=file_id)
    if issuefile is None:
        return False
    
    if request.user not in (issuefile.owner, issuefile.issue.creator,
                            issuefile.issue.project.owner):
        return False

    issuefile.status = consts.FILE_DELETED
    issuefile.save()  
    return True


@login_required
def change_issue(request, name, issue_id):
    if request.method != 'POST':
        return False
    
    st = request.POST.get('op')
    if st == 'del':
        update_status(request, issue_id,
                      consts.ISSUE_DELETED)
        
        return redirect(reverse('apps.issue.views.all_issues', 
                                args=[name]))
        
    elif st == 'close':
        update_status(request, issue_id,
                      consts.ISSUE_CLOSED)
        
    elif st == 'reopen':
        update_status(request, issue_id,
                      consts.ISSUE_OPEN)
        
    return redirect(reverse('apps.issue.views.view_issue', 
                            args=[name, issue_id]))
