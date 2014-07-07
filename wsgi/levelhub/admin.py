from django.contrib import admin

from levelhub.models import UserProfile, Lesson, LessonRequest, LessonReg, LessonRegLog, Message, LessonMessage, UserMessage

# Register your models here.
admin.site.register([UserProfile, Lesson, LessonRequest, LessonReg, LessonRegLog, Message, LessonMessage, UserMessage])