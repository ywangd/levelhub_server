import json

import django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from levelhub.forms import UserSignupForm
from levelhub.models import Lesson, LessonReg, LessonRegLog, Message


def is_json_request(request):
    if 'json' in request.POST or 'json' in request.GET:
        return True
    else:
        return False


def add_header(func):
    def func_header_added(request):
        response = func(request)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Max-Age'] = '120'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Methods'] = 'HEAD, GET, OPTIONS, POST, DELETE'
        response['Access-Control-Allow-Headers'] = 'origin, content-type, accept, x-requested-with'
        return response

    return func_header_added


def home(request):
    return render(request, 'home/home.html', {'version': django.VERSION})


@csrf_exempt
def register(request):
    if request.method == 'POST':
        jq = is_json_request(request)
        signup_form = UserSignupForm(data=request.POST)

        if signup_form.is_valid():
            user = signup_form.save()
            password = user.password
            user.set_password(password)
            user.save()
            user = authenticate(username=user.username, password=password)
            login(request, user)
            if jq:
                return HttpResponse(json.dumps({'user': user.username,
                                                'sessionid': request.session.session_key}))
            else:
                return HttpResponseRedirect('/')
        else:
            if jq:
                err = {}
                for field in signup_form:
                    if len(field.errors) > 0:
                        err[field.html_name] = field.errors[0]
                return HttpResponse(json.dumps({'err': err}))
            else:
                print 'signup_form.errors', signup_form.errors

    else:
        signup_form = UserSignupForm()

    return render(request,
                  'home/register.html',
                  {'signup_form': signup_form})


@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        jq = is_json_request(request)
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            if jq:
                return HttpResponse(json.dumps({'user': str(user),
                                                'sessionid': request.session.session_key}),
                                    content_type='application/json')
            else:
                return HttpResponseRedirect('/')
        else:
            if jq:
                return HttpResponse(json.dumps({'err': 'Invalid login'}),
                                    content_type='application/json')

            return HttpResponse('Invalid login')

    else:
        return render(request, 'home/login.html', {})


@login_required
@csrf_exempt
def user_logout(request):
    print 'logging out ...'
    logout(request)
    if is_json_request(request):
        return HttpResponse(json.dumps({}),
                            content_type='application/json')
    else:
        return HttpResponseRedirect('/')

@csrf_exempt
def debug_reset_db(request):
    if request.method == 'POST':
        User.objects.exclude(username='admin').delete()
        user = User(username='test')
        user.set_password('test')
        user.save()

        Lesson.objects.all().delete()
        lesson = Lesson(teacher=user,
                        name='Folk Guitar Basics',
                        description='An introductory lesson for people who want to pick up guitar fast with no previous experience')
        lesson.save()

        LessonReg.objects.all().delete()
        lesson_reg_1 = LessonReg(lesson=lesson,
                                 student_first_name='Emma',
                                 student_last_name='Wang')
        lesson_reg_1.save()
        lesson_reg_2 = LessonReg(lesson=lesson,
                                 student_first_name='Tia',
                                 student_last_name='Wang')
        lesson_reg_2.save()

        LessonRegLog.objects.all().delete()
        lesson_reg_logs_1 = [LessonRegLog(lesson_reg=lesson_reg_1,
                                          use_time='2014-06-22 15:30:00' if i < 14 else None) for i in range(25)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_1)
        lesson_reg_logs_2 = [LessonRegLog(lesson_reg=lesson_reg_2,
                                          use_time='2014-06-22 15:30:00' if i < 3 else None) for i in range(5)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_2)

        if is_json_request(request):
            return HttpResponse(json.dumps({}),
                                content_type='application/json')
        else:
            return HttpResponseRedirect('/')

    else:
        return HttpResponse('<form method="post" action="/debug_reset_db/"><button type="submit">Reset DB</button><form>')

