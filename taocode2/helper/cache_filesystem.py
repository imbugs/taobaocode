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


from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import BaseLoader, make_origin, get_template_from_string
from django.utils._os import safe_join

import os
import time

__author__ = 'luqi@taobao.com'


class Loader(BaseLoader):
    is_usable = True
    cached = {}
    max_cache = 1024
    
    def get_template_sources(self, template_name, template_dirs=None):
        """
        Returns the absolute paths to "template_name", when appended to each
        directory in "template_dirs". Any paths that don't lie inside one of the
        template dirs are excluded from the result set, for security reasons.
        """
        if not template_dirs:
            template_dirs = settings.TEMPLATE_DIRS
        for template_dir in template_dirs:
            try:
                yield safe_join(template_dir, template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of this particular
                # template_dir (it might be inside another one, so this isn't
                # fatal).
                pass

    def load_template(self, template_name, template_dirs=None):
        return self.load_template_source(template_name, template_dirs)

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                file = open(filepath)
            except IOError:
                tried.append(filepath)
                continue
            
            st = os.fstat(file.fileno())
            cf = self.cached.get(filepath, [-1,-1, None])
            try:
                if cf[0] != st.st_mtime or cf[1] != st.st_size:
                    fdata = file.read().decode(settings.FILE_CHARSET)
                    origin = make_origin(filepath, self.load_template_source, template_name, template_dirs)
                    t = get_template_from_string(fdata, origin, template_name)
                    cf = [st.st_mtime, st.st_size, t, time.time()]
                    self.cached[filepath] = cf
                    
                    if len(self.cached) > self.max_cache:
                        v = min(self.cached.iteritems(), lambda v: v[1][3])
                        del self.cached[v[0]]
                return (cf[2], filepath)  #template
            finally:
                file.close()

        if tried:
            error_msg = "Tried %s" % tried
        else:
            error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
        raise TemplateDoesNotExist(error_msg)
    load_template_source.is_usable = True

_loader = Loader()

def load_template_source(template_name, template_dirs=None):
    # For backwards compatibility
    import warnings
    warnings.warn(
        "'django.template.loaders.filesystem.load_template_source' is deprecated; use 'django.template.loaders.filesystem.Loader' instead.",
        PendingDeprecationWarning
    )
    return _loader.load_template_source(template_name, template_dirs)
load_template_source.is_usable = True
