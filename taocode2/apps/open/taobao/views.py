# coding=utf-8
import logging
from django.shortcuts import redirect
from opens.BaseAPI import ApiError
from opens.taobao.api import TaobaoApi, AUTH_SANDBOX_URL
from apps.open.userlogin import open_user_login, open_new_user_checkin, open_user_binding
from helper.utils import q_get, send_response
from taocode2.models import *

import settings

__author__ = '<a href="mailto:quan.jonny@gmail.com">Jonny</a>'

def do_login(request):
    redirect_to = request.GET.get("next")
    
    taobao = TaobaoApi(consts.TAOBAO_APP_KEY, consts.TAOBAO_APP_SECRET)
    
    authUrl=None
    if settings.TAOBAO_APP_IS_SANDBOX:
        authUrl=taobao.getAuthorizationUrl(AUTH_SANDBOX_URL)
    else:
        authUrl=taobao.getAuthorizationUrl()
        
    return redirect(authUrl)

def do_login_callback(request):
    logger = logging.getLogger('django')
    top_appkey=request.GET.get("top_appkey")
    top_parameters =request.GET.get('top_parameters')
    top_session=request.GET.get('top_session')
    top_sign=request.GET.get('top_sign')
    encode=request.GET.get('encode')
    
    taobao = TaobaoApi(consts.TAOBAO_APP_KEY, consts.TAOBAO_APP_SECRET,sessionkey=top_session)
    
    if taobao.validate_sign(top_parameters,top_sign) is False:
        raise ApiError('Sign Errorr')
    
    topParams=taobao.decodeTopParams(top_parameters)
    open_id=topParams['visitor_id']
    nick=topParams['visitor_nick']
    if 'visitor_role' in topParams:
        visitor_role=topParams['visitor_role']
        if visitor_role == 5:
            return redirect("/login/")

    user=q_get(User,openId=open_id,openPlatform=consts.OPEN_PLATFORM_TAOBAO)
    if user is None:
        rc=request.rc
        rc.topParams=topParams
        rc.session_key=top_session
        return send_response(request, 'open/taobao/login_ext.html')
    else:
        ip=request.META['REMOTE_ADDR']
        tbuser=taobao.GetUserInfo(nick)
        ret=open_user_login(request,open_id,consts.OPEN_PLATFORM_TAOBAO,ip,tbuser.avatar)
        if ret is False:
            return redirect(reverse("apps.main.views.index"))
        else:
            return redirect(reverse('apps.user.views.view_user'))

def do_login_ext(request):
    if request.method=="POST":
        username=request.POST.get("name")
        nick=request.POST.get("nick")
        email=request.POST.get("email")
        openId=request.POST.get("openId")
        session_key=request.POST.get('session_key')
        password=consts.OPEN_DEFAULT_PWD
        bind_type=request.POST.get('bind_account')
        bind_password=request.POST.get('bind_password')
        ip=request.META['REMOTE_ADDR']
        if bind_type is None:
            taobao = TaobaoApi(consts.TAOBAO_APP_KEY, consts.TAOBAO_APP_SECRET, session_key)
            tbuser=taobao.GetUserInfo(nick)

            open_new_user_checkin(openId,username,email,consts.OPEN_PLATFORM_TAOBAO,ip,tbuser.avatar,password=password)
        else:
            user=None
            if bind_type =='name':
                user=q_get(User,name=username)
            elif bind_type =='email':
                user=q_get(User,email=email)
            if user is not None and user.password==secpwd(bind_password):
                open_user_binding(openId,consts.OPEN_PLATFORM_TAOBAO,user)
                ## 
        ret=open_user_login(request,openId,consts.OPEN_PLATFORM_TAOBAO,ip)
        if ret is False:
            return redirect(reverse("apps.main.views.index"))
        else:
            return redirect(reverse('apps.user.views.view_user'))
