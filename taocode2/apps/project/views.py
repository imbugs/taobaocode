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


import sys

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import *
from django.db.models import Q, Count

from taocode2.models import *
from taocode2.helper.utils import *

from taocode2.helper import consts
from taocode2.helper.page import build_page
from taocode2.settings import SITE_ROOT
from taocode2.apps.user.activity import get_prj_activitys

from taocode2.apps.project.forms import NewProjectForm
from taocode2.apps.project.admin import can_access, build_prj_nav_menu
from taocode2.apps.user import activity
from taocode2.apps.repos import svn

from random import randint

__author__ = ['luqi@taobao.com',
              'canjian@taobao.com']

def update_my_project_status(request, projects):
    if request.user.is_authenticated() is False:
        return

    for project in projects:
        project.member_count = q_gets(ProjectMember, project = project, 
                                      user__status = consts.USER_ENABLE).aggregate(members = Count('id'))['members']
        project.watcher_count = q_gets(ProjectWatcher, project = project, 
                                       user__status = consts.USER_ENABLE).aggregate(watchers = Count('id'))['watchers']

        if project.owner == request.user:
            project.my_status = consts.MY_PROJECT_OWNER
        else:
            pm = q_get(ProjectMember, project=project, user=request.user)
            if pm is not None and pm.member_type == consts.PM_ACCEPT_INV:
                project.my_status = consts.MY_PROJECT_MEMBER
                continue
            pw = q_get(ProjectWatcher, project=project, user=request.user)
            if pw is not None:
                project.my_status = consts.MY_PROJECT_WATCH
                continue
            project.my_status = consts.MY_PROJECT_NONE

def build_body_nav_menu(pt):
    bodymenus = [{'uri':'/all/', 'text':'All'},
                 {'uri':'/hot/', 'text':'Most hot'},
                 {'uri':'/newest/', 'text':'Newest'},
                 {'uri':'/random/', 'text':'Random'},
                 {'uri':'/watched/', 'text':'Popular Watched'}]
    
    for v in  bodymenus:
        if v['uri'].find(pt) != -1:
            v['choice'] = True
            break
    return bodymenus

def all_projects(request, pagenum=1, key=None):
    rc = request.rc
    rc.pagename = 'Projects'
    rc.bodymenus = build_body_nav_menu('all')

    pagenum = int(pagenum)
    if request.method == 'POST':
        q = request.POST.get('q', None)
        return redirect(SITE_ROOT + '/all/1/'+q)

    #
    # get project 
    #
    if key is not None:
        q = Q(name__icontains=key) | Q(title__icontains=key)
    else:
        q = Q()

    q = q & Q(status = consts.PROJECT_ENABLE, is_public=True)
    key_text = key and key.encode('utf8') or ''


    build_page(rc, Project, q,
               pagenum, '/all', key_text, order=['-ctime'])

    update_my_project_status(request, 
                             rc.page.object_list)
    
    rc.all_projects = True
    rc.prjs = rc.page.object_list
    rc.key_text = key_text
    return send_response(request, 
                         'project/list.html')


PC = 15

def list_projects(request, pt):
    rc = request.rc
    rc.pagename = 'Projects'
    rc.bodymenus = build_body_nav_menu(pt)

    q = Q(status = consts.PROJECT_ENABLE, is_public=True, )
    od = []
    if pt == 'hot':
        ps = Activity.objects.filter(project__status = consts.PROJECT_ENABLE, 
                                     project__is_public=True).values('project')\
                                     .annotate(Count('project')).order_by('-project__count')[:PC]
        prjs = sort_models(Project, ps, 
                           'project', 'project__count')
    
    elif pt == 'newest':
        prjs = Project.objects.filter(status = consts.PROJECT_ENABLE,
                                      is_public=True).order_by('-ctime')[:PC]
    elif pt == 'random':
        prj_count = Project.objects.filter(status = consts.PROJECT_ENABLE,
                                           is_public=True).count()
        
        pos = randint(0,prj_count)
        
        prjs = Project.objects.filter(status = consts.PROJECT_ENABLE,
                                      is_public=True)[pos:pos+10]
    elif pt == 'watched':
        ps = ProjectWatcher.objects.filter(project__status = consts.PROJECT_ENABLE, 
                                           project__is_public=True).values('project')\
                                           .annotate(Count('project')).order_by('project__count')[:PC]
        prjs = Project.objects.filter(pk__in = [h['project'] for h in ps])

    update_my_project_status(request, prjs)

    rc.prjs = prjs
    return send_response(request, 
                         'project/list.html')

def view_project(request, name):
    return redirect(reverse('apps.repos.views.browse', args=[name]))

def project_info(request, name):
    project = q_get(Project, name=name)

    resp = can_access(project, request.user)
    if resp != None:
        return resp
    
    rc = request.rc
    rc.pagename = 'Info'
    rc.project = project
    rc.logs = get_prj_activitys(project)

    rc.members = q_gets(ProjectMember, project = project, 
                        member_type = consts.PM_ACCEPT_INV)

    update_my_project_status(request, [project])

    rc.navmenus = build_prj_nav_menu(request, project, 'info')

    rc.REPOS = svn.REPOS(name, '/trunk')

    return send_response(request, 'project/view.html')

@login_required
def new_project(request):
    rc = request.rc
    rc.pagename = "Create project."
    rc.pagedesc = "Don't Repeat Yourself (DRY)"
    if request.method != 'POST':
        rc.form = NewProjectForm()
        return send_response(request, 'project/new.html')
    
    form = NewProjectForm(request.POST)
    if form.is_valid() is False:
        rc.form = form
        return send_response(request, 'project/new.html')

    cd = form.cleaned_data

    project = form.save(commit=False)
    project.owner = request.user
    project.status = consts.PROJECT_ENABLE
    project.name = project.name.lower()
    project.save()

    activity.new_prj(project, request.user)
    
    svn.init_repos(project.name)
 
    return redirect(reverse('apps.project.views.view_project', args=[project.name]))


def project_watch_list(request, name):
    return send_response(request, 'project/watch_list.html')


@as_json
@login_required
def watch_project(request, name):
    project = q_get(Project, name=name)

    resp = can_access(project, request.user)
    if resp != None:
        return False

    pw = q_get(ProjectWatcher, project=project, user=request.user)
    
    if pw is None:
        pw = ProjectWatcher(user = request.user,
                            project = project)
        pw.save()
        activity.watch_prj(project, request.user)
        result_text = 'unwatch'
    else:
        pw.delete()
        result_text = 'watch'

    rs = ProjectWatcher.objects.filter(project = project).aggregate(watchers = Count('id'))

    return (True, (result_text, rs['watchers']))


def view_old(request, pid):
    prj = q_get(OldProject, oldid=int(pid))
    if prj is None:
        return redirect(reverse('apps.project.views.all_projects', args=[]))
    
    return redirect(reverse('apps.project.views.view_project', args=[prj.name]))

def view_old_src(request, pid):
    prj = q_get(OldProject, oldid=int(pid))
    if prj is None:
        return redirect(reverse('apps.project.views.all_projects', args=[]))
    
    return redirect(reverse('apps.repos.views.browse', args=[prj.name]))

def view_old_wiki(request, name, path):
    if path == 'ZhWikiStart':
        path = 'index'
    return redirect(reverse('apps.wiki.views.wiki_content', args=[name, path]))
