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
from django.utils.translation.trans_real import gettext

from taocode2.models import User
from taocode2.helper.validator import UniqueValidator, fast_validator
from taocode2.helper.utils import as_json, q_get
from taocode2.helper import consts

from taocode2.settings import SITE_ROOT
from django.core.validators import validate_slug

from django import forms

__author__ = 'luqi@taobao.com'


class NewUserForm(forms.ModelForm):
    name = forms.CharField(label=gettext("user id"),
                           min_length = 3,
                           max_length = 32,
                           help_text=gettext("login account"),
                           validators=[validate_slug,
                                       UniqueValidator(User, 'name')])
    
    #nick = forms.CharField(label=gettext("nick name"),
    #                       min_length = 2,
    #                       max_length = 32,
    #                       help_text=gettext("display name"),
    #                       validators=[validate_slug,
    #                                   UniqueValidator(User, 'nick')])
        
    password_0 = forms.CharField(label=gettext("password"),
                                 min_length = 6,
                                 max_length = 12,
                                 required=False,
                                 widget=forms.PasswordInput)

    password_1 = forms.CharField(label=gettext("password(replay)"),
                                 min_length = 6,
                                 max_length = 12,
                                 required=False,
                                 help_text=gettext("password must same as twice"),
                                 widget=forms.PasswordInput)

    email = forms.EmailField(label=gettext("email address"),
                             help_text=gettext("eg:user@example.org"),
                             validators=[UniqueValidator(User, 'email')])

    accept = forms.BooleanField(label=gettext("accept privacy"),
                                error_messages={'required': gettext('must accept privacy')},
                                help_text="<a href='/about/privacy/' target='_blank'>privacy</a>")
    
    def clean_password_1(self):
        pw0 = self.cleaned_data['password_0']
        pw1 = self.cleaned_data['password_1']
        if pw0 != pw1 or len(pw0) == 0 is True:
            raise forms.ValidationError(gettext('password must same as twice'))
        
        return pw1
        
    class Meta:
        model = User
        fields = ('name', 'password_0', 'password_1', 'email')

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=gettext("E-mail"), max_length=75)

    def clean_email(self):
        email = self.cleaned_data["email"]
        self.cache_user = q_get(User, email__iexact=email,
                                 status=consts.USER_ENABLE)

        if self.cache_user is None:
            raise forms.ValidationError(gettext("That e-mail address doesn't have an associated user account. Are you sure you've registered?"))
        return email
