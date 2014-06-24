from django.db import models
from django.contrib.auth.models import User

from levelhub.utils import utcnow


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    avatar = models.ImageField(upload_to='avatar', null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    data = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.user.username


class Lesson(models.Model):
    teacher = models.ForeignKey(User)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=1024, null=True)
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class LessonReg(models.Model):
    lesson = models.ForeignKey(Lesson)
    student = models.ForeignKey(User, null=True, blank=True)
    student_first_name = models.CharField(max_length=30)
    student_last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(null=True, blank=True)

    def __unicode__(self):
        if self.student is not None:
            return '%s - %s' % (self.lesson.name, self.student.username)
        else:
            return '%s - %s %s' % (self.lesson.name, self.student_first_name, self.student_last_name)


class LessonRegLog(models.Model):
    lesson_reg = models.ForeignKey(LessonReg)
    use_time = models.DateTimeField(null=True, blank=True)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s' % (self.lesson_reg, self.use_time)


class Message(models.Model):
    lesson = models.ForeignKey(Lesson)
    sender = models.ForeignKey(User)
    body = models.TextField(max_length=256)
    creation_time = models.DateTimeField(default=utcnow)
    data = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s - %s' % (self.lesson, self.body, self.sender)