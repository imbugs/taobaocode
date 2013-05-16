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
from taocode2.helper.utils import *

from taocode2.models import *
from taocode2.apps.user.forms import PasswordResetForm
from taocode2.apps.user.verify import new_reset_password_task, check_task
from taocode2.apps.user.views import build_user_nav_menu

from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.decorators import login_required


__author__ = 'luqi@taobao.com'


@login_required
def change_password(request):
    rc = request.rc
    rc.pagename = "Change password"
    rc.navmenus = build_user_nav_menu('newpwd')

    if request.method != 'POST':
        rc.form = PasswordChangeForm(user=request.user)
        return send_response(request, "user/change_password.html")
    
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid() is False:
        rc.form = form
        return send_response(request, "user/change_password.html")

    form.save()
    return send_response(request, "user/change_password_done.html")

def reset_password(request):
    rc = request.rc
    rc.pagename = "Reset password"
    if request.method != 'POST':
        rc.form = PasswordResetForm()
        return send_response(request, "user/password_reset_form.html")
    
    form = PasswordResetForm(request.POST)
    
    if form.is_valid() is False:        
        rc.form = form
        return send_response(request, "user/password_reset_form.html")


    rc.email = form.cleaned_data['email']
    
    new_reset_password_task(form.cache_user)
    
    return send_response(request, "user/password_reset_check.html")

@check_task
def reset_password_code(request, code):
    rc = request.rc
    rc.pagename = "Reset password"
    if request.method != 'POST':
        rc.form = SetPasswordForm(user = rc.task.user)
        return send_response(request, 'user/password_reset.html')
    
    form = SetPasswordForm(user = rc.task.user, data=request.POST)
    if form.is_valid() is False:
        rc.form = form
        return send_response(request, 'user/password_reset.html')
    
    form.save()
    rc.task.is_done = True
    rc.task.save()

    return send_response(request, 'user/password_reset_done.html')


