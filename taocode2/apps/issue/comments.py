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

from taocode2.models import *
from taocode2.helper.utils import *

from taocode2.helper import consts
from taocode2.settings import SITE_ROOT
from taocode2.apps.project.admin import can_access
from taocode2.apps.user import activity

from django.db.models import Q

__author__ = 'luqi@taobao.com'


@as_json
@login_required
def new_comment(request, issue_id):
    
    if request.method != 'POST':
        return False
    
    c = request.POST.get('c', None)
    
    if c is None or len(c) <= 0:
        return False
    
    issue = q_get(Issue, pk = issue_id)

    if issue is None:
        return False
    
    if issue.status != consts.ISSUE_OPEN:
        return False

    if can_access(issue.project, 
                  request.user) != None:
        return False


    return True

@as_json
def get_comments(request, issue_id):
    issue = q_get(Issue, pk=issue_id)
    if issue is None:
        return False

    if issue.status == consts.ISSUE_DELETED:
        return False

    if can_access(issue.project, 
                  request.user) != None:
        return False

    comments = q_gets(IssueComment, issue=issue, status = consts.COMMENT_ENABLE)
    return (True, [(c.id, c.owner.name,  escape(c.content), 
                    str(c.ctime), str(c.mtime)) for c in comments])


@as_json
def del_comment(request):
    if request.method != 'POST':
        return False

    comment_id = request.POST.get('comment_id')

    comment = q_get(IssueComment, pk=comment_id)
    if comment is None:
        return False

    if comment.issue.status != consts.ISSUE_OPEN:
        return False
    
    if request.user not in (comment.issue.project.owner, comment.owner):
        return False

    comment.status = consts.COMMENT_DELETED    

    activity.del_comment(comment.issue.project, 
                         request.user, 
                         comment)
    return True

@as_json
def edit_comment(request, comment_id):
    comment = q_get(IssueComment, pk=comment_id)
    if comment is None:
        return False

    if comment.issue.status != consts.ISSUE_OPEN:
        return False
    
    if request.user not in (comment.issue.project.owner, comment.owner):
        return False
     
    c = request.POST.get('c', None)
    if c is None:
        return False
    
    comment.content = c
    comment.save()    

    activity.edit_comment(comment.issue.project, 
                          request.user, 
                          comment)
    return True
