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
from django.http import *
from django.views.static import serve

from taocode2.helper.utils import *
from taocode2.helper import consts
from taocode2.models import *
from taocode2.apps.project.admin import can_access, can_write
from taocode2 import settings

import urllib

import datetime, time, re, os

__author__ = 'luqi@taobao.com'

safe_re = re.compile(r'(\.|/|\\)')

def safe_ext(f):
    ext = os.path.splitext(f)[1].lower()

    return ext in ('.exe', '.com', '.bat')


def get_upload_root():
    if settings.UPLOAD_DIR[0] == '/':
        d = settings.UPLOAD_DIR
    else:
        d = os.path.join(os.getcwd(), settings.UPLOAD_DIR)
    return d

def get_file_name(ftype, ftid, f):
    d = os.path.join(get_upload_root(), 
                     str(datetime.date.today()))
    
    if os.path.exists(d) is False:
        try:
            os.makedirs(d)
        except:
            pass

    f = safe_re.sub('_',f) # safe filename
    return os.path.join(d,str(time.time()).replace('.','_') + '_%s_%s_%s'%(ftype, ftid, f))

def add_file(request, prj, ftype, ftid, f):
    if safe_ext(f.name) is True:
        return
    
    fname = get_file_name(ftype, ftid, f.name)
    
    open(fname, 'w').write(f.read())
    
    att = ProjectAttachment()
    att.project = prj
    att.ftype = ftype
    att.ftid = ftid
    att.owner = request.user
    att.status = consts.FILE_ENABLE
    att.fname = os.path.relpath(fname, get_upload_root())
    att.orig_name = os.path.split(f.name)[1]
    att.size = f.tell()
    att.save()
    
def get_file(request, name, fid):
    item = q_get(ProjectAttachment, id=int(fid))

    if item is None or item.status != consts.FILE_ENABLE:
        raise Http404
    
    resp = can_access(item.project, request.user)
    if resp is not None:
        return resp


    return serve(request, item.fname, get_upload_root())

@as_json
def del_file(request):

    if request.method != 'POST':
        return (False, 'Need POST')

    fid = request.POST.get('fid')
    if fid is None:
        return (False, 'Need fid')
    
    f = q_get(ProjectAttachment, pk=int(fid))

    if f is None:
        return (False, 'File not found')
    
    if can_write(f.project, request.user) is False:        
        return (False, 'Forbidden')

    f.status = consts.FILE_DELETED
    f.save()

    return True
