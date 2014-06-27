import json

from django.db import models
from django.contrib.auth.models import User

from levelhub.utils import utcnow


JSON_NULL = json.dumps({})

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    # avatar = models.ImageField(upload_to='avatar', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s' % (self.user.id, self.user.username)

    def dictify(self, update_with=None):
        d = {'user_id': self.user.id,
             'username': self.user.username,
             'first_name': self.user.first_name,
             'last_name': self.user.last_name,
             'email': self.user.email,
             'data': self.data}
        if update_with is not None:
            d.update(update_with)
        return d


class Lesson(models.Model):
    teacher = models.ForeignKey(User)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=1024, null=True)
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s' % (self.id, self.name)

    def dictify(self, update_with=None):
        d = {'lesson_id': self.id,
             'name': self.name,
             'description': self.description,
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
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        if self.student is not None:
            return '%d - %s - %s' % (self.id, self.lesson.name, self.student.username)
        else:
            return '%d - %s - %s %s' % (self.id, self.lesson.name, self.student_first_name, self.student_last_name)

    def dictify(self, update_with=None):
        d = {'reg_id': self.id,
             'student': self.student.dictify() if self.student else None,
             'student_first_name': self.student_first_name,
             'student_last_name': self.student_last_name,
             'creation_time': self.creation_time,
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
             'use_time': self.use_time,
             'creation_time': self.creation_time,
             'data': self.data}
        return d


class Message(models.Model):
    lesson = models.ForeignKey(Lesson)
    sender = models.ForeignKey(User)
    body = models.TextField(max_length=256)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(default=JSON_NULL)

    def __unicode__(self):
        return '%d - %s - %s - %s' % (self.id, self.lesson, self.body, self.sender)

    def dictify(self):
        d = {'message_id': self.id,
             'lesson_id': self.lesson.id,
             'sender_id': self.sender.id,
             'body': self.body,
             'creation_time': self.creation_time,
             'data': self.data}
        return d