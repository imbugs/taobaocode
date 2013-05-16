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

from django.core.exceptions import ValidationError
from django.forms.widgets import Input
from taocode2.helper.utils import is_exist, as_json

__author__ = 'luqi@taobao.com'

class UniqueValidator:
    def __init__(self, model, field_name):
        self.m = model
        self.n = field_name

    def __call__(self, value):
        if is_exist(self.m, **{self.n: value}):
            raise ValidationError('the "%s" has exists'%value)

def fast_validator(fvs, uri, f):
    fields = getattr(f, 'declared_fields', None)
    if fields is None:
        return
    for k,v in fields.iteritems():
        if isinstance(v.widget, Input) and v.widget.is_hidden is False:
            u =  f.__name__.lower() + '_' + k
            if hasattr(v, '__fast_validator__'):
                continue
            setattr(v, '__fast_validator__', True)
            fvs[u] = v.clean
            
            v.widget.attrs['onblur'] = "javascript:__fclean('%s/%s/', '__clean_%s__');"%(uri, u, u)

            old_render = v.widget.render

            class RenderProxy:
                def __init__(self, u, old_render):
                    self.u = u
                    self.old_render = old_render
                def render(self, name, value, attrs = None):
                    text = self.old_render(name, value, attrs)
                    return "<span id='__clean_%s__'>%s<span id='clean_result'></span></span>"%(self.u, text)
            
            v.widget.render = RenderProxy(u, v.widget.render).render
            

def fclean(request, fvs, fid):
    if request.method != 'POST':
        return
    
    cfunc = fvs.get(fid, None)

    if cfunc is None:
        return (False, 'not found validator [%s]'%fid)
    v = request.POST.get('v', '').strip()
    try:
        cfunc(v)
    except ValidationError,e:
        return (False, e.messages)
    return (True, '')
