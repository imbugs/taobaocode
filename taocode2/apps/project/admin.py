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
from django.core.urlresolvers import reverse
from django.http import *
from django import forms
from django.db.models import Count,Sum,Q

from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper.func import wrap
from taocode2.helper import consts
from taocode2.apps.user import activity
from taocode2.apps.repos import svn

from taocode2.settings import *
import time


__author__ = 'luqi@taobao.com'


def build_prj_nav_menu(request, project, choice = None):
    uri = '/p/'+project.name

    navmenus = [{'uri': uri + '/src', 'txt':'source'},
                {'uri': uri + '/issues', 'txt':'issues'},
                {'uri': uri + '/wiki', 'txt':'wiki'},
                {'uri': uri + '/info', 'txt':'info'}]

    if project.owner == request.user:
        navmenus.append({'uri': uri + '/admin', 'txt':'admin'})

    if choice is None:
        navmenus[0]['choice'] = True
    else:
        for m in navmenus:
            if m['uri'].endswith(choice):
                m['choice'] = True
    return navmenus

def need_owner(view_func):
    def _wrapped_view(request, *args, **kwargs):
        rc = request.rc
        rc.project = q_get(Project, name=kwargs['name'],
                           status = consts.PROJECT_ENABLE)
        rc.project_name = kwargs['name']

        if rc.project == None:
            raise Http404

        if rc.project.owner != request.user:
            if request.user.supper is False:
                return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrap(view_func, _wrapped_view)

def can_access(prj, user):
    if prj is None or prj.status != consts.PROJECT_ENABLE:
        raise Http404

    if prj.is_public:
        return None

    if user.is_authenticated() is False:
        return HttpResponseForbidden()

    if prj.owner != user:
        pm = q_get(ProjectMember, project = prj, user = user)
        if pm is None:
            return HttpResponseForbidden()
    return None


def can_write(prj, user):
    if prj is None or prj.status != consts.PROJECT_ENABLE:
        return False

    if user.is_authenticated() is False:
        return False

    if prj.owner != user:
        pm = q_get(ProjectMember, project = prj, user = user)
        if pm is None:
            return False
    return True
    

@need_owner
@as_json
@login_required
def do_invite(request, name):
    if request.method != 'POST':
        return False
    uname = request.POST.get('u', '').strip()
    if len(uname) <= 0:
        return False
    
    user = q_get(User, Q(name=uname)|Q(email=uname))
    if user is None or user == request.user:
        return False

    rc = request.rc

    pm = q_get(ProjectMember,
               project=rc.project, user=user)
    
    if pm is not None:
        if pm.member_type != consts.PM_ACCEPT_INV:
            pm.member_type = consts.PM_SEND_INV
            pm.save()
        return True
    
    pm = ProjectMember()
    pm.project = rc.project
    pm.user = user
    pm.member_type = consts.PM_SEND_INV
    pm.save()

    return True

@login_required
@need_owner
def project_admin(request, name):
    rc = request.rc
    rc.pagename = name + ' admin'
    uri = request.META['PATH_INFO']
    
    #rc.navmenus = [{'uri': uri, 'txt':'basic', 'choice':True},
    #               {'uri': uri + 'resources', 'txt':'resources'}]

    rc.navmenus = build_prj_nav_menu(request, rc.project, 'admin')

    res = []
    vls = q_gets(Issue, project = rc.project,
                 status__in = (consts.ISSUE_OPEN, 
                               consts.ISSUE_CLOSED)).values('project').annotate(pc=Count('project'))
    res.append(['Issue Count', 
                len(vls) > 0 and vls[0]['pc'] or 0])
    vls = q_gets(ProjectAttachment, project = rc.project,
                 status = consts.FILE_ENABLE).values('project').annotate(pc=Count('project'))

    res.append(['Attachemts Count',
                len(vls) > 0 and vls[0]['pc'] or 0])
    
    vls = q_gets(ProjectAttachment,
                 project = rc.project,
                 status = consts.FILE_ENABLE).values('project').annotate(ps=Sum('size'))
    
    si = (len(vls) > 0 and vls[0]['ps'] or 0) / (1024*1024.0)
    
    res.append(['Attachemts Total Size','%.4s MB'%si])

    r,out, err = exec_cmd(['du','-sbh', os.path.join(settings.REPOS_ROOT, name)])
    res.append(['Repository Usage', r != 0 and '0.0 MB' or out.split()[0]])

    rc.res = res

    rc.licenses = map(lambda x:x[0], consts.LICENSES)
    if rc.project.status != consts.PROJECT_ENABLE:
        raise Http404

    return send_response(request, 'project/admin.html')


@login_required
@need_owner
def project_resources(request, name):
    rc = request.rc
    rc.pagename = 'Project resources usages'
    uri = '/p/'+name+'/admin'
    
    rc.navmenus = [{'uri': uri, 'txt':'basic'},
                   {'uri': uri + 'resouces',
                    'txt':'resources', 'choice':True}]

    if rc.project.status != consts.PROJECT_ENABLE:
        raise Http404

    return send_response(request, 'project/resources.html')


@as_json
def get_members(request, name):
    project = q_get(Project, name=name)
    if project is None:
        return False
    
    resp = can_access(project, request.user)
    if resp is not None:
        return False

    members = q_gets(ProjectMember, project=project) 
    return (True, [m.json() for m in members])

def do_invite_op(request, name, op):
    if request.method != 'POST':
        return False

    project = q_get(Project, Q(name=name))

    if project is None:
        return False
    pm = q_get(ProjectMember, project=project, user=request.user)

    if pm is None:
        return False

    pm.member_type = op
    pm.save()

    if op == consts.PM_ACCEPT_INV:
        activity.join_member(project, request.user, request.user)

    return True

@as_json
@login_required
def do_accept(request, name):
    return do_invite_op(request, name, 
                        consts.PM_ACCEPT_INV)

@as_json
@login_required
def do_reject(request, name):
    return do_invite_op(request, name,
                        consts.PM_REJECT_INV)

@as_json
@login_required
def do_exit(request, name):
    
    project = q_get(Project, name = name)
    
    if project is None:
        return False
    
    ProjectMember.objects.filter(project = project,
                                 user = request.user).delete()

    activity.leave_member(project, request.user, request.user)
    return True

@login_required
@need_owner
@as_json
def del_member(request, name):
    if request.method != 'POST':
        return False
    
    uname = request.POST.get('u', '').strip()
    if len(uname) <= 0:
        return False

    rc = request.rc

    ProjectMember.objects.filter(project = rc.project,
                                 user = User.objects.filter(name=uname)).delete()
    return True


@login_required
@need_owner
@as_json
def del_prj(request, name):
    if request.method != 'POST':
        return False
    
    del_name = name + '__DELETED__%s'%time.time()

    project = request.rc.project
    old_name = project.name

    project.name = del_name
    project.status = consts.PROJECT_MARK_DELETED
    project.save()
    
    svn.del_repos(old_name, del_name)
    
    return (True, reverse('apps.user.views.view_user', args=[]))

@login_required
@need_owner
@as_json
def edit_prj(request, name):
    if request.method != 'POST':
        return False
    
    project = request.rc.project
    title = request.POST.get('t','').strip()
    
    if len(title) <= 0:
        return False
    
    license = request.POST.get('l','').strip()
    is_public = request.POST.get('pub','0').strip()
    project.title = title
    project.license =  license
    project.is_public = bool(int(is_public))
    project.save()

    return True


