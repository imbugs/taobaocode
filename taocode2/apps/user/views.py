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
from django.utils.translation import gettext

from taocode2.helper import consts

from taocode2.models import *
from taocode2.apps.user.forms import NewUserForm
from taocode2.apps.user.verify import new_change_email_task

from taocode2.helper.utils import *

from taocode2.settings import SITE_ROOT
from taocode2.apps.user.activity import get_user_activitys
from django.conf import settings
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME
from django.http import *

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from django.forms import ValidationError

from django.db.models import Count,Q
from django.core.urlresolvers import reverse
from django.core.validators import slug_re, email_re

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect

import urlparse

__author__ = 'luqi@taobao.com'

def build_user_nav_menu(choice = None):
    uri = '/my/'

    navmenus = [{'uri': '/my', 'txt':'My'},
                {'uri': '/my/edit', 'txt':'Change profile'},
                {'uri': '/my/newpwd', 'txt':'Change Password'}]

    if choice is None:
        navmenus[0]['choice'] = True
    else:
        for m in navmenus:
            if m['uri'].endswith(choice):
                m['choice'] = True
    return navmenus

def login_view(request):
    redirect_to = request.REQUEST.get("next", '')

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]

            # Use default setting if redirect_to is empty
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Security check -- don't allow redirection to a different
            # host.
            elif netloc and netloc != request.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
                
            if request.POST.get('remember', None) is not None:
                request.session.set_expiry(604800)# 7* 24*3600
                    
            return redirect(redirect_to)
    else:
        form = AuthenticationForm(request)

    request.session.set_test_cookie()

    rc = request.rc

    rc.form = form
    rc.next = redirect_to

    return send_response(request, 'user/login.html')


def logout_view(request):
    auth_logout(request)
    redirect_to = request.REQUEST.get('next', '')

    if redirect_to:
        netloc = urlparse.urlparse(redirect_to)[1]
        # Security check -- don't allow redirection to a different host.
        if not (netloc and netloc != request.get_host()):
            return redirect(redirect_to)

    return redirect(reverse('apps.main.views.index'))

def register(request):
    rc = request.rc
    rc.pagename = "Create your account."
    if request.method != 'POST':
        rc.form = NewUserForm()
        return send_response(request, 'user/register.html')
    
    form = NewUserForm(request.POST)
    if form.is_valid() is False:
        rc.form = form
        return send_response(request, 'user/register.html')

    cd = form.cleaned_data
    
    user = form.save(commit=False)
    user.password = secpwd(cd['password_0'])
    user.status = consts.USER_ENABLE
    user.sex = consts.USER_UNKNOWN
    #user.pic = consts.DEFAULT_PIC
    user.last_login_ip = request.META['REMOTE_ADDR']

    user.save()
    
    auser = authenticate(username=cd['name'], password=cd['password_0'])
    if auser is not None and auser.is_active:
        auth_login(request, auser)
        
    return redirect(reverse('apps.user.views.view_user', args=[]))

def view_user(request, name=None):    
    rc = request.rc
    if name is None:
        
        if request.user.is_authenticated():
            name = request.user.name
        else:
            raise Http404
        
    rc.current_user = q_get(User, name=name, status=consts.USER_ENABLE)


    if rc.current_user is None:
        raise Http404


    prj_q = Q(project__status = consts.PROJECT_ENABLE)
    owner_q = Q(owner = rc.current_user, 
                status = consts.PROJECT_ENABLE)
    
    
    if rc.current_user != request.user:
        prj_q = prj_q & Q(project__is_public = True)
        owner_q = owner_q & Q(is_public = True)
        #rc.current_user.my_status = is_exist(UserWatcher, 
        #                                     target = rc.current_user) and 1 or 0
    else:
        rc.navmenus = build_user_nav_menu()

    rc.pagename = rc.current_user.name
        
    rc.owner_projects = Project.objects.filter(owner_q)

    rc.joined_projects = q_gets(ProjectMember, 
                                user = rc.current_user).filter(prj_q).exclude(member_type=consts.PM_REJECT_INV)

    rc.watch_projects = q_gets(ProjectWatcher, 
                               user = rc.current_user).filter(prj_q)
    
    rc.follows = q_gets(UserWatcher, 
                        user = rc.current_user, 
                        target__status = consts.USER_ENABLE)
    
    rc.fans = q_gets(UserWatcher, 
                     target = rc.current_user, 
                     user__status = consts.USER_ENABLE)

    rc.logs = get_user_activitys(rc.current_user, request, 50)
    
    return send_response(request, 'user/view.html')

@login_required
def edit_my(request):
    rc = request.rc
    rc.pagename = "Change profile"

    rc.navmenus = build_user_nav_menu('edit')
    return send_response(request, 'user/edit_my.html')

@login_required
def edit_notify(request):
    rc = request.rc
    rc.pagename = "Change notify"

    uri = request.META['PATH_INFO']

    return send_response(request, 'user/edit_notify.html')


@as_json
@login_required
def do_edit_my(request):
    if request.method != 'POST':
        return False
    return True

@as_json
@login_required
def do_edit_email(request):
    if request.method != 'POST':
        return False
    
    e = request.POST.get('e', '').strip()
    if len(e) <= 0 or e == request.user.email:
        return False

    if not email_re.search(e):
        return False
     
    new_change_email_task(request.user, e)
    #
    #
    return True


@as_json
@login_required
def watch_user(request, name):
    target = q_get(User, name=name, status=consts.USER_ENABLE)
    if target is None:
        return False

    uw = q_get(UserWatcher, target=target, user=request.user)
    
    if uw is None:
        uw = UserWatcher(user = request.user,
                         target = target)
        uw.save()
        result_text = 'unfollow'
    else:
        uw.delete()
        result_text = 'follow'

    rs = UserWatcher.objects.filter(target = target).aggregate(watchers = Count('id'))

    return (True, (result_text, rs['watchers']))

@as_json
def check_name(request, name):
    target = q_get(User, name=name)
    if target is None:
        return True
    return False

@as_json
def check_email(request, email):
    target = q_get(User, email=email)
    if target is None:
        return True
    return False

@as_json
def check_email_auth(request):
    if request.method=='POST':
        email=request.POST.get('email')
        pwd=request.POST.get('pwd')
        target = q_get(User, email=email)

        if target is None:
            return (False,gettext('Email Not Exist'))

        return target.password == secpwd(pwd)
    else:
        return (False,gettext('InValid Request'))

@as_json
def check_name_auth(request):
    if request.method=='POST':
        name=request.POST.get('name')
        pwd=request.POST.get('pwd')
        target = q_get(User, name=name)

        if target is None:
            return (False,gettext('Name Not Exist'))

        return target.password == secpwd(pwd)
    else:
        return (False,gettext('InValid Request'))
