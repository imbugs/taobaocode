from django.conf.urls.defaults import patterns, include

u = ['',
     ('imok/$', 'api.project.imok'),
     ('hot_prjs/$', 'api.project.hot_prjs'),
     ('new_prjs/$', 'api.project.new_prjs'),
     ('hot_users/$', 'api.project.hot_users'),
     ('last_logs/$', 'api.project.last_logs'),
     ]

urlpatterns = patterns(*u)
