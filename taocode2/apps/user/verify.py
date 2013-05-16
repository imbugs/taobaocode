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

from taocode2.helper import consts

from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper.mail import send_mail
from taocode2.helper.func import wrap

from django.conf import settings
from django.contrib.auth.decorators import login_required

from hashlib import md5
from random import random
import datetime, time

__author__ = 'luqi@taobao.com'

def new_reset_password_task(user):
    expire = datetime.timedelta(settings.PASSWORD_RESET_TIMEOUT_DAYS, 
                                0, 0)
    code = new_verify_task(user, 'reset-password', '', expire)
    
    send_mail(user.email, 'Reset your password!',
              'mail/reset_password.html',
              {'user':user, 'code':code})

    
def new_change_email_task(user, new_email):
    expire = datetime.timedelta(settings.PASSWORD_RESET_TIMEOUT_DAYS, 
                                0, 0)
    code = new_verify_task(user, 'change-email', new_email, expire)
    
    send_mail(new_email, 'Change your email!',
              'mail/change_email.html',
              {'user':user, 'code':code})

def new_verify_task(user, name, data, expire):
    VerifyTask.objects.filter(user=user, name=name).update(is_done=True)
    
    task = VerifyTask()
    task.user = user

    ht = name + str(user.id)
    ht += str(random()) + str(time.time())

    task.code = md5(ht).hexdigest()
    task.name = name
    task.data = data
    task.expire_time = datetime.datetime.now() + expire # timedelta
    task.save()
        
    return task.code


def check_task(view_func):
    def _wrapped_view(request, *args, **kwargs):
        rc = request.rc

        task = q_get(VerifyTask, code=kwargs['code'])
        if task is None:
            return HttpResponseForbidden()
        
        rc = request.rc
        if task.is_done:
            rc.verify_fail = 'the task is done'
            return send_response(request, 'user/verify/fail.html')
        
        n = datetime.datetime.now()
        if n > task.expire_time:    
            rc.verify_fail = 'the task is expire at %s'%(task_expire_time)
            return send_response(request, 'user/verify/fail.html')

        rc.task = task

        return view_func(request, *args, **kwargs)
    return wrap(view_func, _wrapped_view)


@check_task
def reset_password(request, code):
    rc = request.rc
    raise 'TODO:'
    
@login_required
@check_task
def check_code(request, code):
    rc = request.rc
    rc.pagename = "Verify code"
    return do_task_next(request, rc.task)
  
def do_task_next(request, task):
    rc = request.rc

    if task.name == 'change-email':
        rc.pagename = "Change email"
        return send_response(request, 'user/verify/change_email.html')
 
@login_required
@check_task
def do_check_code_cancel(request, code):
    rc = request.rc
    rc.pagename = "Verify code"
    rc.task.is_done = True
    rc.task.save()
    if rc.task.name == 'change-email':
        rc.verify_cancel = 'The email not change yet!'
    return send_response(request, 'user/verify/cancel.html')

@login_required
@check_task
def do_check_code_ok(request, code):
    rc = request.rc
    rc.pagename = "Verify code"
    rc.task.is_done = True
    rc.task.save()
    
    if rc.task.name == 'change-email':
        request.user.email = rc.task.data
        request.user.save()
        rc.verify_ok = 'The email change with '+ rc.task.data
        return send_response(request, 'user/verify/ok.html')
