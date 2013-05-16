from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url('^weibo/login/$', 'apps.open.weibo.views.do_login'),
    url('^weibo/login/ext/$', 'apps.open.weibo.views.do_login_ext'),
    url('^weibo/login/callback/$', 'apps.open.weibo.views.do_login_callback'),
    url('^taobao/login/$', 'apps.open.taobao.views.do_login'),
    url('^taobao/login/ext/$', 'apps.open.taobao.views.do_login_ext'),
    url('^taobao/login/callback/$', 'apps.open.taobao.views.do_login_callback'),
)