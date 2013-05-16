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

from django import template
from django.utils.translation import ugettext as _
from taocode2.settings import SITE_ROOT
from taocode2.models import WikiContent, ProjectAttachment, Project
from taocode2.helper.utils import q_get, q_gets, utc2loc
from taocode2.helper import consts
from django.utils.encoding import smart_str, smart_unicode
from hashlib import md5
import urllib

from django.core.urlresolvers import reverse
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe


register = template.Library() 

@register.simple_tag
def gravatar(email, alt='', size=48):
    url = "http://www.gravatar.com/avatar/"+md5(email).hexdigest()
    url += '?s='+str(size)

    return """<img src="%s" width="%s" height="%s" title="%s" border="0"/>""" % (url, size, size, alt)

def choice(value, arg):
    args = dict([a.strip().split(':') for a in arg.split(',')])
    v = unicode(value)
    return args.get(v,v)

def show_url(value, arg=None):
    c = 'url'
    if arg is not None:
        c += '_'+arg
    return getattr(value, c)()


from taocode2.apps.wiki.parser import to_html

class WikiContext:
    def __init__(self, prj, wiki):
        self.prj = prj
        self.wiki = wiki
        self.req = None
        self.href = prj.url()
        self.base_url = 'http://code.taobao.org'
        self.resource = None
        self.perm = None
    def get_hint(self, n, default=None):
        return default
    
    def img_resolver(self, target):
        if self.wiki is None:
            return target
        vals = target.split(':',2)
        files = []
        if len(vals) == 1 and self.wiki is not None:
            files = q_gets(ProjectAttachment,project = self.prj, ftid = self.wiki.id,
                           ftype = 'wiki',
                           orig_name = target,
                           status = consts.FILE_ENABLE)
        elif len(vals) == 2:
            return target
        elif len(vals) == 3:
            if vals[0].lower() != 'wiki':
                return target

            wiki = q_get(WikiContent, project = self.prj, path = vals[1])

            if wiki is not None:
                files = q_gets(ProjectAttachment,project = self.prj, ftid = wiki.id,
                               ftype = 'wiki',
                               orig_name = vals[2],
                               status = consts.FILE_ENABLE)
                
        if len(files) > 0:
            f = files[0]
            return '%sfile/%s/%s'%(f.project.url(), f.id, f.orig_name)

        return target

    def link_resolver(self, ns, target):
        if ns != 'wiki':
            return None
        v = target.split(' ', 1)

        if len(v) == 2:
            target = v[0]

        wiki = q_get(WikiContent, project = self.prj, path = target)

        if wiki is not None:
            return True, wiki.url()

        return False, reverse('apps.wiki.views.wiki_content',
                              args=[self.prj.name, target])
        
       
def tracwiki(s, val):
    if type(val) is WikiContent:
        ctx = WikiContext(val.project, val)
    elif type(val) is Project: 
        ctx = WikiContext(val, None)
       
    return mark_safe(to_html(s, ctx))


def truncatechars(v, l):
    if v is None:
        return None
    if len(v) > l:
        return v[:l] + '...'
    return v

register.filter('utc2loc', utc2loc)
register.filter('truncatechars', truncatechars)
register.filter('wikitext', tracwiki)
register.filter('choice', choice)
register.filter('url', show_url)
