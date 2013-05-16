from taocode2.models import Project, User, Activity, FeatureProject
from taocode2.helper import consts
from django.db.models import Count, Sum

from taocode2.apps.user.activity import get_user_activitys
from taocode2.helper.utils import *
from django.core import serializers


def to_json(objs, fields = None):
    data = serializers.serialize("json", objs, fields = fields, use_natural_keys=True)
    return HttpResponse(data, mimetype='application/json')

def hot_prjs(request):
    hps = Activity.objects.filter(project__status=consts.PROJECT_ENABLE,
                                  project__is_public=True).values('project').annotate(pc = Count("project")).order_by('-pc')[:10]
    
    hot_prjs = sort_models(Project, hps, 
                           'project', 'pc')
    
    return to_json(hot_prjs)

def new_prjs(request):
    prjs = Project.objects.filter(status=consts.PROJECT_ENABLE,
                                  is_public=True).order_by('-ctime')[:10]
    
    return to_json(prjs)

def hot_users(request):
    aus = Activity.objects.filter(user__status=consts.USER_ENABLE,
                                  project__status=consts.PROJECT_ENABLE,
                                  project__is_public=True).values('user').annotate(uc = Count("user")).order_by('-uc')[:20]
    
    ausers = sort_models(User, aus, 
                         'user', 'uc')
    
    return to_json(ausers, fields = ('name', 'email', 'last_login'))

def last_logs(request):
    logs = get_user_activitys(None, request, 50, False)
    return to_json(logs)


def imok(request):
    return HttpResponse("yes, imok!")
