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


from django.db.models import Q
from django.core.paginator import Paginator

__author__ = 'luqi@taobao.com'

def build_page(rc, model, q, pagenum, prefix,
               key_text='',              
               page_arg='page',
               count_arg='result_count',
               page_count=10,
               order=None):
    
    if order is not None: 
        result = Paginator(model.objects.filter(q).order_by(*order), page_count)
    else:
        result = Paginator(model.objects.filter(q), page_count)

    pagenum = min(max(pagenum, 1), result.num_pages)
    
    page = result.page(pagenum)

    rc.first_page_uri = '{0}/1/{1}'.format(prefix, key_text);
    rc.last_page_uri = '{0}/{1}/{2}'.format(prefix, 
                                            result.num_pages, 
                                            key_text)

    if page.has_previous():
        rc.previous_page_uri = '{0}/{1}/{2}'.format(prefix,
                                                    pagenum - 1,
                                                    key_text)

    if page.has_next():
        rc.next_page_uri = '{0}/{1}/{2}'.format(prefix,
                                                pagenum + 1,
                                                key_text)
    
    
    setattr(rc, page_arg, page)
    setattr(rc, count_arg, result.count)

