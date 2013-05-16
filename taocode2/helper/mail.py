# -*- coding: utf-8 -*-
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


from django.core.mail import send_mail as send_out_email
from taocode2.settings import MAIL_SENDER, TEAM_NAME, SITE_URL 
from django.template.loader import render_to_string

__author__ = 'luqi@taobao.com'


def send_mail(target, title, template_file, context):

    context.update({'TEAM_NAME':TEAM_NAME,
                    'SITE_URL':SITE_URL})

    body = render_to_string(template_file, context)
    
    send_out_email(title, body, MAIL_SENDER,
                   [target], fail_silently=False)
    
