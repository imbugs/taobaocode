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

from taocode2.models import User, secpwd
from taocode2.helper import consts
from django.db.models import Q

__author__ = 'luqi@taobao.com'

class UserAuthBackend:
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(Q(name__iexact=username) | Q(email__iexact=username),
                                    status = consts.USER_ENABLE)            
        except User.DoesNotExist:
            return None
                
        if secpwd(password) != user.password:
            return None
        
        return user

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None

    def has_perm(self, user, perm):
        return False
    
    def supports_object_permissions(self):
        return False

    def supports_anonymous_user(self):
        return False
