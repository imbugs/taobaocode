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

from taocode2.models import Project, User, Activity, FeatureProject
from taocode2.helper import consts
from django.db.models import Count, Sum

from taocode2.apps.user.activity import get_user_activitys
from taocode2.helper.utils import *
from django.core.cache import cache
from random import randint

__author__ = 'luqi@taobao.com'

def index(request):
    rc =  request.rc

    ev = cache.get('index_cache')

    if ev is None:
        rc.new_projects = Project.objects.filter(status=consts.PROJECT_ENABLE,
                                                 is_public=True).order_by('-ctime')[:6]

        hps = Activity.objects.filter(project__status=consts.PROJECT_ENABLE,
                                      project__is_public=True).values('project').annotate(pc = Count("project")).order_by('-pc')[:6]

        rc.hot_projects = sort_models(Project, hps, 
                                      'project', 'pc')

        aus = Activity.objects.filter(user__status=consts.USER_ENABLE,
                                      project__status=consts.PROJECT_ENABLE,
                                      project__is_public=True).values('user').annotate(uc = Count("user")).order_by('-uc')[:10]

        rc.ausers = sort_models(User, aus, 
                                'user', 'uc')
        
        rc.feature_prjs = FeatureProject.objects.all().order_by('-mtime')[:5]
        rc.logs = get_user_activitys(None, request, 10, False)
        ev = {}
        ev['new_projects'] = rc.new_projects
        ev['hot_projects'] = rc.hot_projects
        ev['ausers'] = rc.ausers 
        
        ev['feature_prjs'] = rc.feature_prjs
        ev['logs'] = rc.logs

        cache.set('index_cache', ev, 60) #60secs

    rc.new_projects = ev['new_projects']
    rc.hot_projects = ev['hot_projects']
    rc.ausers = ev['ausers']
    
    rc.feature_prjs = ev['feature_prjs']
    rc.logs = ev['logs']

    prj_count = Project.objects.filter(status = consts.PROJECT_ENABLE,
                                       is_public=True).count()
    pos = randint(0,prj_count)
    random_prjs = Project.objects.filter(status = consts.PROJECT_ENABLE,
                                         is_public=True)[pos:pos+10]

    rc.random0_projects = random_prjs[:5]
    rc.random1_projects = random_prjs[5:]
    
    return send_response(request, 'index.html')

def show_page(request, name, pagename=''):
    request.rc.pagename = pagename
    return send_response(request, name)
