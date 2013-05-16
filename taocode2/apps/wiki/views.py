from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper import consts

from django.http import *
from django.db.models import Count, Q
from django.shortcuts import render_to_response, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from taocode2.models import WikiContent, WikiContentLog
from taocode2.apps.project.admin import can_access, can_write
from taocode2.apps.project.views import build_prj_nav_menu
from taocode2.apps.project import prj_key
from taocode2.apps.main.files import add_file

from difflib import unified_diff

def safe_esc(v):
    return v

def wiki_formarts(request):
    rc = request.rc
    rc.pagename ='Wiki Formarts'
    rc.formarts = 'formarts'
    return send_response(request, 
                         'wiki/formarts.html')

def edit_wiki(request, name, path=None):
    project = q_get(Project, name=name)

    can_op = can_write(project, request.user)
    if can_op is False:
        return HttpResponseForbidden()
    
    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')
    
    rc.can_op = can_op
    
    rc.pagename = 'Edit [' + path +']'
    
    wiki = q_get(WikiContent, project=project, path=path)
    
    if request.method == 'POST':
        doval = request.POST.get('do',None)
        if doval == 'preview':
            #
            rc.content = request.POST.get('content')
            rc.preview =  safe_esc(rc.content)
            rc.wiki = wiki
            if rc.wiki is None:
                rc.wiki = project
        elif doval == 'save':
            # create page
            if wiki is None:
                wiki = WikiContent()
                wiki.project =  project
                wiki.path = path
                wiki.status = consts.WIKI_ENABLE
                wiki.user = request.user
                old_content = None

            else:
                old_content = wiki.content

            wiki.last_user = request.user
            wiki.content = request.POST.get('content')
            
            if wiki.content != old_content:
                wiki.save()
                            
                log = WikiContentLog(project = project,
                                     user = request.user,
                                     wiki = wiki,
                                     content = wiki.content,
                                     old_content = old_content)
                log.save()

            return redirect(reverse('apps.wiki.views.wiki_content', args=[name, path]))
            
    else:
        wiki = q_get(WikiContent, project=project, path=path)
        if wiki is not None:
            rc.content = wiki.content
        
    return send_response(request, 
                         'wiki/edit.html')

    
def wiki_index(request, name):
    #list all page
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp

    path = prj_key.get(project, prj_key.WIKI_INDEX, 'index')
   
    return redirect(reverse('apps.wiki.views.wiki_content', args=[name, path]))

def wiki_content(request, name, path):
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp


    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')

    rc.pagename = path
                            
    rc.can_op = can_write(project, request.user)
    rc.wiki = q_get(WikiContent, project = project, path=path)

    if request.method == 'POST' and rc.can_op:
        atts = request.FILES.getlist('attachment')
        fc = 0

        for f in atts:
            if fc <= prj_key.get(project, prj_key.UPLOAD_LIMIT_COUNT, 5):
                add_file(request, project, 'wiki', rc.wiki.id, f)
                fc += 1

    if rc.wiki is not None:
        rc.wiki.content = safe_esc(rc.wiki.content)

        rc.files = q_gets(ProjectAttachment, project = project, 
                          ftype = 'wiki',
                          ftid = int(rc.wiki.id),
                          status = consts.FILE_ENABLE).order_by('-ctime')
        
    
    return send_response(request, 
                         'wiki/view.html')


def del_wiki(request, name):    
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp
    
    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')
    rc.can_op = can_write(project, request.user)
    
    if request.method == 'POST':
        wiki = q_get(WikiContent, project = project, pk=int(request.POST.get('wiki_id')))
        wiki.delete()
        return redirect(reverse('apps.wiki.views.wiki_index', args=[name]))
        
    return HttpResponseForbidden()

def wiki_changes(request, name, path):  
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp
    
    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')

    rc.pagename = path
    rc.wiki = q_get(WikiContent, project = project, path = path)

    if rc.wiki is not None:
        rc.logs = q_gets(WikiContentLog, wiki = rc.wiki).order_by('-ctime')

    return send_response(request, 
                         'wiki/changes.html')

def wiki_list(request, name):
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp
    
    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')
    rc.wikis = q_gets(WikiContent, project = project)
    return send_response(request, 
                         'wiki/list.html')

def raw_wiki(request, name, path):
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp

    wiki = q_get(WikiContent, project = project, path = path)
    
    if wiki is None:
        raise Http404
    
    return HttpResponse(wiki.content)

def raw_log_wiki(request, name, logid):
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp
    
    log = q_get(WikiContentLog, pk=int(logid))
    
    if log is None:
        raise Http404
    
    return HttpResponse(log.content)

def diff_log_wiki(request, name, logid):
    project = q_get(Project, name=name)
    resp = can_access(project, request.user)
    if resp != None:
        return resp
        
    rc = request.rc
    rc.project = project
    rc.navmenus = build_prj_nav_menu(request, project, 'wiki')
    
    log = q_get(WikiContentLog, pk=int(logid))
    
    if log is None:
        raise Http404

    rc.log = log

    c = log.content
    oldc = log.old_content and log.old_content or ''
    
    diff_text = '\n'.join(unified_diff(oldc.split('\n'), c.split('\n')))
    rc.content = diff_text

    return send_response(request, 
                         'wiki/view_change.html')
