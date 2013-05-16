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

from django.db import models
from hashlib import md5
from django.core.urlresolvers import reverse
from taocode2.helper import consts
from django.utils.html import escape

def secpwd(pwd):
    return md5('%s'%(pwd)).hexdigest()

class User(models.Model):
    name = models.CharField(max_length=32, unique=True)
    #nick = models.CharField(max_length=32, unique=True)
    email = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=128)

    status = models.SmallIntegerField(db_index=True,
                                      choices=[(consts.USER_DISABLE, 'Disable'),
                                               (consts.USER_ENABLE, 'Enable'),
                                               (consts.USER_DELETED, 'Deleted'),
                                               ])
    ctime = models.DateTimeField(auto_now_add=True)
    supper = models.BooleanField(default=False)
    
    #pic = models.CharField(max_length=200)
    sex = models.SmallIntegerField(choices=[(consts.USER_FEMALE, 'Female'),
                                            (consts.USER_MALE, 'Male'),
                                            (consts.USER_UNKNOWN, 'Unknown'),
                                            ])
    
    last_login_ip = models.CharField(max_length=32)
    last_login = models.DateTimeField(auto_now=True)

    openId=models.CharField(max_length=40,blank=True)
    
    openPlatform=models.CharField(max_length=100,blank=True)

    def natural_key(self):
        return self.name
    
    def __unicode__(self):
        return self.name

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.status == consts.USER_ENABLE

    def get_and_delete_messages(self):
        return []

    def check_password(self, raw_password):
        return self.password == secpwd(raw_password)

    def set_password(self, new_password):
        self.password = secpwd(new_password)

    def url(self):
        return reverse('apps.user.views.view_user', args=[self.name])

    def is_staff(self):
        return self.supper
    
    def has_perm(self, label):
        return self.supper

    def has_module_perms(self, label):
        return self.supper

class Message(models.Model):
    owner = models.ForeignKey(User)
    sender = models.ForeignKey(User, related_name="sender", null=True)

    is_read = models.BooleanField()
    sender_status = models.SmallIntegerField()
    reader_status = models.SmallIntegerField()
    
    content = models.CharField(max_length=1024)

    send_time = models.DateTimeField(auto_now_add=True)
    read_time = models.DateTimeField(null=True, blank=True)
    
    def json(self):
        return (self.id, self.sender.url(), self.sender.name,
                self.owner.url(), self.owner.name,
                self.is_read, escape(self.content).replace('\n','<br/>'), 
                str(self.send_time), str(self.read_time))


class Project(models.Model):
    owner = models.ForeignKey(User)

    name = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=200, null=True)
    tags = models.TextField(null=True)

    status = models.SmallIntegerField(db_index=True,
                                      choices = [(consts.PROJECT_DISABLE, 'Disable'),
                                                 (consts.PROJECT_ENABLE, 'Enable'),
                                                 (consts.PROJECT_MARK_DELETED, 'Mark Deleted'),
                                                 (consts.PROJECT_TRUE_DELETED, 'True Deleted')])
    ctime = models.DateTimeField(auto_now_add=True)

    license = models.CharField(max_length=255, null=True,
                               choices = consts.LICENSES)
    is_public = models.BooleanField()
    
    def __unicode__(self):
        return self.name

    def url(self):
        return reverse('apps.project.views.view_project', args=[self.name])

class ProjectProfile(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=32, unique=True)
    value = models.CharField(max_length=1024)
    

class ProjectMember(models.Model):
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    member_type = models.SmallIntegerField(choices = [(consts.PM_SEND_INV, 'Send invitation'),
                                                      (consts.PM_ACCEPT_INV,'Accept invitation'),
                                                      (consts.PM_REJECT_INV,'Reject invitation'),
                                                      ])
    join_time = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "project")]

    
    def get_inv_text(self, inv):
        if inv == consts.PM_SEND_INV:
            return 'Sending'
        elif inv == consts.PM_REJECT_INV:
            return 'Rejected'
        else:
            return 'Accepted'
       
    def json(self):
        return (self.user.url(), self.user.name, 
                self.get_inv_text(self.member_type), str(self.join_time))
    
    def json_join(self):
        return (self.project.url(), self.project.name,
                self.get_inv_text(self.member_type), str(self.join_time))

class ProjectWatcher(models.Model):
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    
    watch_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("user", "project")]

class Repository(models.Model):
    project = models.ForeignKey(Project)

    repos_type = models.SmallIntegerField()
    vc_type=models.SmallIntegerField() #version control type:svn,git..
    url = models.CharField(max_length=1024)
    auth_user = models.CharField(max_length=128)
    auth_password = models.CharField(max_length=128)

class Issue(models.Model):
    project = models.ForeignKey(Project)
    #tracker = models.ForeignKey("Tracker")
    #version = models.ForeignKey("Version", null=True)
    creator = models.ForeignKey(User, related_name="creator", null=True)
    #assigner = models.ForeignKey(User, related_name="assigner", null=True)

    #tags = models.ManyToManyField(blank=True, "Tag", null=True)

    title = models.CharField(max_length=200)
    content = models.TextField(null=True)
    status = models.SmallIntegerField(db_index=True,
                                      choices = [(consts.ISSUE_OPEN,'Open'),
                                                 (consts.ISSUE_CLOSED,'Closed'),
                                                 (consts.ISSUE_DELETED,'Deleted')])
    #start = models.DateTimeField(blank=True,null=True)
    #end = models.DateTimeField(blank=True,null=True)
    
    vote_count = models.IntegerField(blank=True)
    
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    
    def closed(self):
        return self.status == consts.ISSUE_CLOSED

    def url(self):
        return reverse('apps.issue.views.view_issue',
                       args=[self.project.name, self.id])

    def __unicode__(self):
        return self.title

"""
class Tracker(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=64, unique=True)

    def __unicode__(self):
        return self.name

class Version(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=64)

    start = models.DateTimeField()
    end = models.DateTimeField()

    def __unicode__(self):
        return self.name


    class Meta:
        unique_together = [("name", "project")]

"""    
class Tag(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=12, null=True)

    def __unicode__(self):
        return self.name



class IssueComment(models.Model):
    issue = models.ForeignKey(Issue)
    owner = models.ForeignKey(User)
    content = models.TextField()
    
    status = models.SmallIntegerField(choices = [(consts.COMMENT_ENABLE, 'Enable'),
                                                 (consts.COMMENT_DELETED, 'Deleted')])
    
    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.content

class IssueVote(models.Model):
    issue = models.ForeignKey(Issue)
    owner = models.ForeignKey(User)
    ctime = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("issue", "owner")]


class WikiContent(models.Model):
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User)
    last_user = models.ForeignKey(User, related_name="last_user")

    path = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    status = models.SmallIntegerField(choices = [(consts.WIKI_ENABLE, 'Enable'),
                                                 (consts.WIKI_DELETED, 'Deleted')])

    ctime = models.DateTimeField(auto_now_add=True)
    mtime = models.DateTimeField(auto_now=True)

    def url(self):
        return reverse('apps.wiki.views.wiki_content',
                       args=[self.project.name, self.path])

    def __unicode__(self):
        return self.path

    class Meta:
        unique_together = [("project", "path")]


class WikiContentLog(models.Model):
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User)
    wiki = models.ForeignKey(WikiContent)

    content = models.TextField(null=True)
    old_content = models.TextField(null=True)    
    ctime = models.DateTimeField(auto_now_add=True)


class ProjectAttachment(models.Model):    
    project = models.ForeignKey(Project)
    ftype = models.CharField(max_length=12)
    ftid = models.IntegerField()
    status = models.SmallIntegerField(choices = [(consts.FILE_ENABLE, 'Enable'),
                                                 (consts.FILE_DELETED, 'Deleted')])
    fname = models.CharField(max_length=1024)
    orig_name = models.CharField(max_length=255)
    size = models.IntegerField()
    owner = models.ForeignKey(User)
    ctime = models.DateTimeField(auto_now_add=True)

    def json(self):
        return [self.id, escape(self.orig_name)]

    def __unicode__(self):
        return self.orig_name

class VerifyTask(models.Model):
    user = models.ForeignKey(User)

    code = models.CharField(max_length=32, unique=True) #md5code
    name = models.CharField(max_length=255, db_index=True)
    data = models.CharField(max_length=255)

    is_done = models.BooleanField()
    ctime = models.DateTimeField(auto_now_add=True, db_index=True)
    expire_time = models.DateTimeField()
    

class UserWatcher(models.Model):
    user = models.ForeignKey(User)
    target = models.ForeignKey(User, related_name="target", db_index=True)

    watch_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("user", "target")]

class Activity(models.Model):
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User, null=True, blank=True)
    act_type = models.CharField(max_length=32, db_index=True)
    content = models.CharField(max_length=255, null=True, blank=True)
    ctime = models.DateTimeField(db_index=True)

class ReposChecker(models.Model):
    project = models.ForeignKey(Project, unique=True)
    last_rev = models.IntegerField()
    last_time = models.DateTimeField(auto_now=True, db_index=True)

class FeatureProject(models.Model):
    project = models.ForeignKey(Project, unique=True)
    desc = models.TextField()
    mtime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.project.name

class OldProject(models.Model):
    oldid = models.IntegerField(db_index=True)
    name = models.CharField(max_length=32, unique=True)
    
