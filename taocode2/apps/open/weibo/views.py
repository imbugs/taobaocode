# coding=utf-8
import logging
from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.http import urlquote
from opens.weibo.api import WeiboApi
from apps.open.userlogin import open_user_binding
from taocode2.apps.open.userlogin import open_user_login, open_new_user_checkin
from helper.utils import send_response, q_get
from taocode2.models import *

import settings

__author__ = '<a href="mailto:quan.jonny@gmail.com">Jonny</a>'

def do_login(request):
    weibo = WeiboApi(consts.WEIBO_APP_KEY, consts.WEIBO_APP_SECRET)
    temp_credentials = weibo.getRequestToken()
    cache.set(temp_credentials['oauth_token'], temp_credentials['oauth_token_secret'])
    callback_url=settings.SITE_URL+"/open/weibo/login/callback/"
    callback_url=urlquote(callback_url)
    authUrl=weibo.getAuthorizationURL(temp_credentials['oauth_token'],oauth_callback=callback_url)
    return redirect(authUrl)

def do_login_callback(request):
    logger = logging.getLogger('django')
    oauth_token=request.GET.get("oauth_token")
    oauth_verifier=request.GET.get('oauth_verifier')
    if cache.get(oauth_token) is None:
        return redirect("/login/")
    
    weibo = WeiboApi(consts.WEIBO_APP_KEY, consts.WEIBO_APP_SECRET)
    
    temp_credentials = {'oauth_callback_confirmed': 'true'}
    temp_credentials['oauth_token']=oauth_token
    temp_credentials['oauth_token_secret']=cache.get(oauth_token)
    cache.delete(oauth_token)
    access_token = weibo.getAccessToken(temp_credentials, oauth_verifier)
    weibo.SetCredentials(consts.WEIBO_APP_KEY, consts.WEIBO_APP_SECRET,access_token['oauth_token'],access_token['oauth_token_secret'])
    logger.debug("access_token:%s"%access_token)

    open_id=access_token['user_id']
    user=q_get(User,openId=open_id,openPlatform=consts.OPEN_PLATFORM_WEIBO)
    if user is None:
        rc=request.rc
        rc.access_token=access_token
        user=weibo.GetUser(open_id)
        rc.openUser=user
        
        return send_response(request, 'open/wb/login_ext.html')
    else:
        ip=request.META['REMOTE_ADDR']
        weiboUser=weibo.GetUser(open_id)
        ret=open_user_login(request,open_id,consts.OPEN_PLATFORM_WEIBO,ip,weiboUser.profile_image_url)
        if ret is False:
            return redirect(reverse("apps.main.views.index"))
        else:
            return redirect(reverse('apps.user.views.view_user'))

def do_login_ext(request):
    if request.method=="POST":
        username=request.POST.get("name")
        email=request.POST.get("email")
        openId=request.POST.get("openId")
        oauth_token=request.POST.get("oauth_token")
        oauth_token_secret=request.POST.get("oauth_token_secret")
        bind_type=request.POST.get('bind_account')
        bind_password=request.POST.get('bind_password')
        password=consts.OPEN_DEFAULT_PWD
        ip=request.META['REMOTE_ADDR']
        if bind_type is None:
            weibo = WeiboApi(consts.WEIBO_APP_KEY, consts.WEIBO_APP_SECRET, oauth_token, oauth_token_secret)

            weiboUser=weibo.GetUser(openId)

            open_new_user_checkin(openId,username,email,consts.OPEN_PLATFORM_WEIBO,ip,weiboUser.profile_image_url,password=password)
        else:
            user=None
            if bind_type =='name':
                user=q_get(User,name=username)
            elif bind_type =='email':
                user=q_get(User,email=email)
            if user is not None and user.password==secpwd(bind_password):
                open_user_binding(openId,consts.OPEN_PLATFORM_WEIBO,user)
                ## 
        ret = open_user_login(request,openId,consts.OPEN_PLATFORM_WEIBO,ip)
        if ret is False:
            return redirect(reverse("apps.main.views.index"))
        else:
            return redirect(reverse('apps.user.views.view_user'))
