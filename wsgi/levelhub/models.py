import json
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

from levelhub.utils import utcnow
from levelhub.consts import *


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    # avatar = models.ImageField(upload_to='avatar', null=True, blank=True)
    website = models.URLField(blank=True)
    about = models.CharField(max_length=1024)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s' % (self.user.id, self.user.username)

    def dictify(self, update_with=None):
        d = {'user_id': self.user.id,
             'username': self.user.username,
             'first_name': self.user.first_name,
             'last_name': self.user.last_name,
             'display_name': (self.user.username if self.user.first_name == '' and self.user.last_name == ''
                              else ' '.join([self.user.first_name, self.user.last_name])),
             'email': self.user.email,
             'about': self.about,
             'last_login': datetime.strftime(self.user.last_login, "%Y-%m-%d %H:%M:%SZ"),
             'creation_time': datetime.strftime(self.user.date_joined, "%Y-%m-%d %H:%M:%SZ"),
             'data': self.data}
        if update_with is not None:
            d.update(update_with)
        return d


class Lesson(models.Model):
    teacher = models.ForeignKey(User)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=1024)
    status = models.IntegerField(default=LESSON_ACTIVE)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s' % (self.id, self.name)

    def dictify(self, update_with=None):
        d = {'lesson_id': self.id,
             'teacher': self.teacher.get_profile().dictify(),
             'name': self.name,
             'description': self.description,
             'status': self.status,
             'creation_time': self.creation_time,
             'data': self.data}
        if update_with is not None:
            d.update(update_with)
        return d


class LessonReg(models.Model):
    lesson = models.ForeignKey(Lesson)
    student = models.ForeignKey(User, null=True, blank=True)
    student_first_name = models.CharField(max_length=30)
    student_last_name = models.CharField(max_length=30)
    status = models.IntegerField(default=LESSON_REG_ACTIVE)
    creation_time = models.DateTimeField(default=utcnow)
    daytimes = models.CharField(max_length=512)  # comma separated class times
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        if self.student is not None:
            return '%d - %s - %s' % (self.id, self.lesson.name, self.student.username)
        else:
            return '%d - %s - %s %s' % (self.id, self.lesson.name, self.student_first_name, self.student_last_name)

    def dictify(self, update_with=None):
        d = {'reg_id': self.id,
             'lesson_id': self.lesson.id,
             'student': self.student.get_profile().dictify() if self.student else None,
             'student_first_name': self.student_first_name,
             'student_last_name': self.student_last_name,
             'status': self.status,
             'creation_time': self.creation_time,
             'daytimes': self.daytimes,
             'data': self.data}
        if update_with is not None:
            d.update(update_with)
        return d


class LessonRegLog(models.Model):
    lesson_reg = models.ForeignKey(LessonReg)
    use_time = models.DateTimeField(null=True, blank=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s - %s' % (self.id, self.lesson_reg, self.use_time)

    def dictify(self):
        d = {'rlog_id': self.id,
             'lesson_reg_id': self.lesson_reg.id,
             'use_time': self.use_time,
             'creation_time': self.creation_time,
             'data': self.data}
        return d


class Message(models.Model):
    sender = models.ForeignKey(User)
    body = models.TextField(max_length=256)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s - %s' % (self.id, self.body, self.sender)

    def dictify(self):
        d = {'message_id': self.id,
             'sender': self.sender.get_profile().dictify(),
             'body': self.body,
             'creation_time': self.creation_time,
             'data': self.data}
        return d


class LessonMessage(models.Model):
    lesson = models.ForeignKey(Lesson)  # the lesson for receiving the message
    message = models.ForeignKey(Message)

    def __unicode__(self):
        return '%d - %s - %s' % (self.id, self.lesson, self.message)

    def dictify(self):
        d = {'lesson': self.lesson.dictify(),
             'message': self.message.dictify()}
        return d


class UserMessage(models.Model):
    user = models.ForeignKey(User)  # the recipient user of the message
    message = models.ForeignKey(Message)

    def __unicode__(self):
        return '%d - %s - %s' % (self.id, self.user, self.message)

    def dictify(self):
        d = {'user': self.user.dictify(),
             'message': self.message.dictify()}
        return d


class LessonRequest(models.Model):
    sender = models.ForeignKey(User, related_name='lesson_request_sender')
    receiver = models.ForeignKey(User, related_name='lesson_request_receiver')
    lesson = models.ForeignKey(Lesson)
    message = models.CharField(max_length=256)
    status = models.IntegerField()
    daytimes = models.CharField(max_length=512)
    is_new = models.BooleanField(default=True)
    creation_time = models.DateTimeField(default=utcnow)

    def __unicode__(self):
        return '%s -> %s [%d]' % (self.sender.username, self.receiver.username, self.status)

    def dictify(self):
        d = {'req_id': self.id,
             'sender': self.sender.get_profile().dictify(),
             'receiver': self.receiver.get_profile().dictify(),
             'lesson': self.lesson.dictify(),
             'message': self.message,
             'status': self.status,
             'daytimes': self.daytimes,
             'creation_time': self.creation_time}
        return d
