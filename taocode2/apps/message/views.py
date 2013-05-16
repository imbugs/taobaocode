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


from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper.page import build_page
from taocode2.helper import consts

from django.utils.html import escape
from django.db.models import Count, Q
from django.core.paginator import Paginator

__author__ = 'luqi@taobao.com'


navitems = (('inbox', '/msg/inbox', 'inbox'),
            ('outbox', '/msg/outbox', 'outbox'),
            ('trashbox', '/msg/trashbox', 'trashbox'),)

@login_required
def show_box(request, name='inbox', pagenum=1):
    #
    #
    if name not in ('inbox', 'outbox', 'trashbox'):
        name = 'inbox'

    rc = request.rc
    rc.pagename = name
    rc.boxname = name

    rc.navmenus = build_menu(navitems, name)

    if name == 'inbox':#inbox
        q = Q(owner = request.user, 
              reader_status = consts.MSG_READER_INBOX)
        order = ('is_read', '-send_time')
    elif name == 'outbox': #outbox
        q = Q(sender = request.user, 
              sender_status = consts.MSG_SENDER_OUTBOX)
        order = ('-send_time',)
    else: #trashbox
        q = Q(owner = request.user, 
              reader_status = consts.MSG_READER_TRASHBOX)
        q = q | Q(sender = request.user, 
                  sender_status = consts.MSG_SENDER_TRASHBOX)
        order = ('-read_time',)
     
    build_page(rc, Message, q, int(pagenum), 
               '/msg/'+name, 
               page_count=5,
               order=order)
    
    if name == 'inbox':
        for m in rc.page.object_list:
            if m.is_read is False:
                m.is_read = True
                m.save()
                m.is_read = False
                
    return send_response(request, 'message/list.html')


@as_json
@login_required
def get_unread_count(request):
    msg_result = Message.objects.filter(owner=request.user,
                                        is_read=False).aggregate(Count('is_read'))
    
    count = msg_result.get('is_read__count', 0)
    return (True, count)

@as_json
@login_required
def send_msg(request):
    if request.method != 'POST':
        return False    
    uname = request.POST.get('u','').strip()
    content = request.POST.get('c', '').strip()

    if len(uname) <= 0 or len(content) <= 0:
        return False
    
    reader = q_get(User, name = uname)
    
    if reader is None:
        return False
    
    msg = Message()
    msg.owner = reader
    msg.sender = request.user

    msg.sender_status = consts.MSG_SENDER_OUTBOX
    msg.reader_status = consts.MSG_READER_INBOX
    msg.is_read = False
    msg.content = content
    msg.save()
   
    return True

def check_owner(request):
    if request.method != 'POST':
        return None
    
    msgid = request.POST.get('m','').strip()

    if len(msgid) <= 0: 
        return None
    
    msg = q_get(Message, pk=msgid)
    if msg is None:
        return None

    if request.user not in (msg.owner, msg.sender):
        return None
    
    return msg

@as_json
@login_required
def del_msg(request):
    msg = check_owner(request)
    if msg is None:
        return False

    if msg.owner == request.user:
        msg.reader_status = consts.MSG_DELETED
    else:
        msg.sender_status = consts.MSG_DELETED

    if msg.reader_status == consts.MSG_DELETED and \
            msg.sender_status == consts.MSG_DELETED:
        msg.delete()
    else:
        msg.save()
        
    return True

@as_json
@login_required
def move_msg(request):  
    msg = check_owner(request)
    if msg is None:
        return False
 
    target = request.POST.get('t','').strip()
    if target not in ('inbox', 'outbox', 'trashbox'):
        return False
            
    if msg.owner == request.user:
        if msg.reader_status == consts.MSG_DELETED:
            return False
        if target == 'trashbox':
            msg.reader_status = consts.MSG_READER_TRASHBOX
        else:
            msg.reader_status = consts.MSG_READER_INBOX
    else:
        if msg.sender_status == consts.MSG_DELETED:
            return False

        if target == 'trashbox':
            msg.sender_status = consts.MSG_SENDER_TRASHBOX
        else:
            msg.sender_status = consts.MSG_SENDER_OUTBOX
    
    msg.save()
    return True

