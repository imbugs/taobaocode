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

from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper import consts,xmlo
from taocode2 import settings
import chardet
import os

__author__ = 'luqi@taobao.com'

def init_repos(name):
    if name is None or len(name) <= 0:
        raise Exception('Project name fall ['+name+']')
    
    repos_path = os.path.join(settings.REPOS_ROOT, name)
    r, out, err = exec_cmd(['svnadmin', 'create', repos_path])

    if r != 0:
        raise Exception(err)
    
    #r, out, err = exec_cmd(['chmod', 'o+w', '-R', repos_path])
    #if r != 0:
    #    raise Exception(err)
    
    #if settings.REPOS_POST_HOOK != '':
    #    exec_cmd(['ln', '-s', settings.REPOS_POST_HOOK, 
    #              os.path.join(repos_path,'hooks/post-commit')])
        
    r, out, err = exec_cmd(['svn', 'mkdir', '--no-auth-cache', '--non-interactive',
                            ADMIN_REPOS(name, '/trunk/'),
                            ADMIN_REPOS(name, '/tags/'),
                            ADMIN_REPOS(name, '/branches/'),
                            '-m', 'init '+name])
    if r != 0:
        raise Exception(err)


def del_repos(name, del_name):
    if name is None or len(name) <= 0:
        raise Exception('Project name fall ['+name+']')
    
    repos_path = os.path.join(settings.REPOS_ROOT, name)
    del_repos_path = os.path.join(settings.REPOS_ROOT, del_name)
    
    r, out, err = exec_cmd(['mv', repos_path, del_repos_path])
    
    if r != 0:
        raise Exception(err)
def safe_path(path):
    path = path.strip()
    if path != '/':
        return '/' + path
    return '/'

def REPOS(name, path = ''):
    return settings.REPOS_URL + name + path

def ADMIN_REPOS(name, path = ''):
    return settings.REPOS_ADMIN_URL + name + path

def LIST(url):
    code, out ,err = exec_cmd(['svn', 'list','--xml', '--incremental', 
                               '--no-auth-cache', '--non-interactive', url])
    if code != 0:
        raise Exception(err)
    return xmlo.loads(out) 

def CAT(url):
    code, out ,err = exec_cmd(['svn','cat', '--no-auth-cache', '--non-interactive', url])
    if code != 0:
        raise Exception(err)
    return out

def INFO(url):
    code, out ,err = exec_cmd(['svn','info', '--xml', '--no-auth-cache', '--non-interactive', url])
    if code != 0:
        raise Exception(err)
    return xmlo.loads(out)

def LOG(url, rev=None, limit=-1):
    cmd = 'svn log -v --xml --no-auth-cache --non-interactive'.split(' ')
    if rev is not None:
        cmd.append('-r')
        cmd.append(rev)
    if limit != -1:
        cmd.append('-l')
        cmd.append(str(limit))
    cmd.append(url)
    code, out ,err = exec_cmd(cmd)

    if code != 0:
        raise Exception(err)

    return xmlo.loads(out)
    
def DIFF(url, revN, revM=None):
    cmd = 'svn diff --no-auth-cache --non-interactive --no-diff-deleted'.split(' ')
    if revN is not None and revM is None:
        cmd.append('-c')
        cmd.append(revN)
    elif revN is not None and revM is not None:
        cmd.append('-r')
        cmd.append(revN + ':' + revM)

    cmd.append(url)    
    code, out ,err = exec_cmd(cmd)
    if code != 0:
        return None
    return out

