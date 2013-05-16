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


from django.utils.decorators import available_attrs
try:
    from functools import update_wrapper, wraps
except ImportError:
    from django.utils.functional import update_wrapper, wraps  # Python 2.4 fallback.

__author__ = 'luqi@taobao.com'

def wrap(view_func, _wrapped_view):
    return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
