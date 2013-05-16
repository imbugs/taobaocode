# coding=utf-8
from datetime import datetime
from django.contrib.auth import login as auth_login, authenticate
from django.db.models import Q
from taocode2.helper.utils import q_get
from taocode2.models import *

__author__ = '<a href="mailto:quan.jonny@gmail.com">Jonny</a>'

def open_new_user_checkin(openId,username,email,platform,ip=None,pic=None,password=None):
    
    user=q_get(User, Q(name__iexact=username) | Q(email__iexact=email))
    if user is not None:
        return user
    user=User(name=username,email=email)
    user.openId=openId
    user.openPlatform=platform
    user.last_login_ip=ip
    user.last_login=datetime.now()
    user.set_password(password)
    user.status=consts.USER_ENABLE
    user.sex=consts.USER_UNKNOWN
    user.save()

    return True

def open_user_binding(openId,platform,user):
    user.openId=openId
    user.openPlatform=platform
    user.save()
    return True

def open_user_login(request,openId,platform,ip,pic=None,password=None):
    user=q_get(User,openId=openId,openPlatform=platform)
    if user is not None:
        user.last_login_ip=ip
        user.last_login=datetime.now()
        user.save()
        if password is not None:
            auser = authenticate(username=user.name,password=password)
        else:
            auser = user
            auser.backend = "%s.%s" % ("apps.user.auth","UserAuthBackend")
        auth_login(request, auser)
        return True
    else:
        return False
