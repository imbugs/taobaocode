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

from django import http
from django.conf import settings
import sys
import traceback
import time


__author__ = 'luqi@taobao.com'


def simple_context(request):
    if hasattr(request, 'rc'):
        return request.rc.__dict__
    return {}


class SimpleRequestContext:
    def __init__(self):
        pass

def _get_traceback(self, exc_info=None):
    """Helper function to return the traceback as a string"""
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))

class SimpleContextMiddleware:
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if hasattr(request, 'rc') is False:
            request.rc = SimpleRequestContext()
        return None


    def process_exception_none(self, request, exception):
        if settings.DEBUG:
            return None

        if isinstance(exception, http.Http404):
            return None

        exc_info = sys.exc_info()
        
        try:
            request_repr = repr(request)
        except:
            request_repr = "Request repr() unavailable"
        
        message = "%s\n\n%s" % (_get_traceback(exc_info), request_repr)

        f = file(settings.HOOK_LOGS, 'a+')
        print >>f, 'Exception at',time.ctime()
        print >>f, message
        print >>f
        return None

