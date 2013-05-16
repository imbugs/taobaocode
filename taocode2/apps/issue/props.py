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

from taocode2.models import *
from taocode2.helper.utils import *

from taocode2.helper import consts
from taocode2.helper.page import build_page
from taocode2.settings import SITE_ROOT

from django.db.models import Q

__author__ = 'luqi@taobao.com'


def new_prop(request, name, prop_class, args = []):
    
    project = q_get(Project, name = name,
                    owner = request.user)
    
    if project is None:
        return False
    
    n = request.POST.get('name', None)
    if n is None:
        return False    
    
    if q_get(prop_class, 
             project=project, name=n) is not None:
        return False

    prop = prop_class()
    prop.project = project
    prop.name = n

    for arg in args:
        v = request.POST.get(arg, None)
        if v is not None:
            setattr(prop, arg, v)
    prop.save()
    return (True, [prop.id, n] + [getattr(prop, arg) for arg in args])

def get_props(request, name, prop_class, args = []):
    project = q_get(Project, name = name)
    
    if project is None:
        return (True, [])
    props = q_gets(prop_class, project=project)

    return (True, [[p.id, p.name] + [getattr(p, arg) for arg in args] for p in props])

def del_prop(request, name, prop_class):
    if request.method != 'POST':
        return False

    n = request.POST.get('name', None)
    if n is None:
        return False

    project = q_get(Project, name = name, owner = request.user)

    if project is None:
        return False
    
    prop_class.objects.filter(project = project, name = n).delete()
    return True

"""
@as_json
@login_required
def new_tracker(request, name):
    return new_prop(request, name, Tracker)

@as_json
def get_trackers(request, name):
    return get_props(request, name, Tracker)

@as_json    
@login_required
def del_tracker(request, name):
    return del_prop(request, name, Tracker)

"""
@as_json
@login_required
def new_tag(request, name):
    return new_prop(request, name, Tag, ['color'])

@as_json
def get_tags(request, name):
    return get_props(request, name, Tag, ['color'])

@as_json    
@login_required
def del_tag(request, name):
    return del_prop(request, name, Tag)

