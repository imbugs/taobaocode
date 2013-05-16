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

from taocode2.models import *
from taocode2.helper.utils import q_get, q_gets, utc2loc
from taocode2.helper import consts

from django.db.models import Q
from datetime import datetime

__author__ = 'luqi@taobao.com'

ACT_TEXTS = {
    'new_commit':'Commited',
    'new_prj':'Create Project',
    'watch_prj':'Watch Project',
    'new_issue':'New Issue',
    'close_issue':'Closed Issue',
    'edit_issue':'Update Issue',
    }

def format_activity(act):
    cmd, m = act.act_type.split('_')
    act.cmd = cmd
    act.act_text = ACT_TEXTS.get(act.act_type, act.act_type)
    
    if m == 'issue':
        act.issue = q_get(Issue, pk=int(act.content))
    elif m == 'comment' and cmd != 'del':
        act.comment = q_get(IssueComment, pk=int(act.content))
    elif m == 'commit':
        rev, msg = act.content.split(' ', 1)
        act.commit = {'rev':rev,
                      'msg':msg}

    return act

def get_user_activitys(target, request, limit=0, list_public=True):
    if target is None:
        q = Q()
    else:
        q = Q(user = target)
    if request.user.is_authenticated() and list_public:
        pm_q = ProjectMember.objects.filter(user = request.user).values('project').query
        q = q & Q(Q(project__is_public = True) | Q(project__in = pm_q) | Q(project__owner = request.user))
    else:
        q = q & Q(Q(project__is_public = True))

    q = q & Q(project__status = consts.PROJECT_ENABLE)
    
    if limit <= 0:
        return map(format_activity, Activity.objects.filter(q).order_by('-ctime'))
    else:
        return map(format_activity, Activity.objects.filter(q).order_by('-ctime'))[0:limit]


def get_prj_activitys(project):
    q = Q(project = project)
    return map(format_activity, Activity.objects.filter(q).order_by('-ctime'))

def new_activity(prj, user, atype, content, ctime=None):
    act = Activity()
    act.project = prj
    act.user = user
    act.act_type = atype
    act.content = content
    
    if ctime is not None:
        act.ctime = ctime
    else:
        act.ctime = datetime.today()
    act.save()

def new_prj(prj, user):
    new_activity(prj, user, 'new_prj', str(prj.id))
    
def join_member(prj, user, member):
    pass
    #new_activity(prj, user, 'join_member', str(member.id))

def leave_member(prj, user, member):
    pass
    #new_activity(prj, user, 'leave_member', str(member.id))
     
def new_issue(prj, user, issue):
    new_activity(prj, user, 'new_issue', str(issue.id))

def edit_issue(prj, user, issue):
    pass
    #new_activity(prj, user, 'edit_issue', str(issue.id))

def close_issue(prj, user, issue):
    new_activity(prj, user, 'close_issue', str(issue.id))

def del_issue(prj, user, issue):
    new_activity(prj, user, 'del_issue', str(issue.id))

def reopen_issue(prj, user, issue):
    new_activity(prj, user, 'reopen_issue', str(issue.id))

def new_comment(prj, user, comment):
    pass
    #new_activity(prj, user, 'new_comment', str(comment.id))

def del_comment(prj, user, comment):
    pass
    #new_activity(prj, user, 'del_comment', str(comment.id))

def watch_prj(prj, user):
    pass
    #new_activity(prj, user, 'watch_prj', str(prj.id))

def unwatch_prj(prj, user):
    pass
    #new_activity(prj, user, 'unwatch_prj', str(prj.id))

def new_commit(prj, user, rev, msg, ctime):
    msg = msg.strip()
    if len(msg) <= 0:
        return
    date = ctime.date()
    t    = ctime.time()
    ctime = datetime.combine(date, t)
    new_activity(prj, user, 'new_commit', rev + ' '+ msg, utc2loc(ctime))


