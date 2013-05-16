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

# Django settings for taocode2 project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

REPOS_ROOT = 'svn_root'
REPOS_URL = 'http://127.0.0.1:8080/svn/'
REPOS_ADMIN_URL = 'http://127.0.0.1:8080/adminsvn/'
HOOK_LOGS = 'err_hooks.log'

ADMINS = (
    ('', 'your_email@domain.com'),
)

MAIL_SENDER = 'code@taobao.org'
TEAM_NAME = 'Taocode team'
SITE_URL = 'http://code.taobao.org'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME':'taocode2',  # Or path to database file if using sqlite3.
        'USER': 'root',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'zh-CN'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''
SITE_ROOT  = ''


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

LOGIN_URL = SITE_ROOT + '/login/'
LOGIN_REDIRECT_URL = SITE_ROOT + '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
DEFAULT_CHARSET = 'utf-8'

UPLOAD_DIR='uploads'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    #'taocode2.helper.cache_filesystem.load_template_source',(
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.csrf',
    'django.contrib.auth.context_processors.auth',
    'taocode2.helper.middleware.simple_context',
    'django.contrib.messages.context_processors.messages',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'taocode2.helper.middleware.SimpleContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    )

ROOT_URLCONF = 'taocode2.urls'

TEMPLATE_DIRS = (
    'templates',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.messages',
    'taocode2',
    )

AUTHENTICATION_BACKENDS = (
    'taocode2.apps.user.auth.UserAuthBackend',
    )

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

SECRET_KEY = 'test'
DATETIME_FORMAT='Y-m-d H:i:s'
DATE_FORMAT='Y-m-d'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'


try:
    from private_setting import *
except ImportError:
    pass

TAOBAO_APP_IS_SANDBOX=False
