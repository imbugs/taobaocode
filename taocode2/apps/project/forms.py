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

from taocode2.models import User, Project
from taocode2.helper.validator import UniqueValidator
from taocode2.helper.consts import LICENSES

from django.core.validators import validate_slug

from django import forms
from django.forms import widgets

__author__ = 'luqi@taobao.com'



class NewProjectForm(forms.ModelForm):
    name = forms.CharField(label="name", 
                           min_length = 3,
                           max_length = 32,
                           help_text="project name",
                           validators=[validate_slug, 
                                       UniqueValidator(Project, 'name')])

    title = forms.CharField(label="title", 
                            widget = widgets.TextInput(attrs = {'size':40}),
                            min_length = 3,
                            max_length = 200,
                            required=False,
                            help_text="project title")
    
    license = forms.ChoiceField(label="license",
                                required=False,
                                choices = LICENSES,
                                help_text="project license")

    is_public = forms.BooleanField(label="Is public",
                                   required=False,
                                   help_text="project is public")
    
    class Meta:
        model = Project
        fields = ('name', 'title', 'license', 'is_public')

        
        
