import json

import django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from levelhub.forms import UserSignupForm, UserForm
from levelhub.models import UserProfile, Lesson, LessonReg, LessonRegLog, Message
from levelhub.utils import DateEncoder


def is_json_request(request):
    if request.path.startswith('/j/'):
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


def err_response(message):
    return HttpResponse(json.dumps({"err": message}),
                        content_type='application/json')


def home(request):
    return render(request, 'home/home.html', {'version': django.VERSION})


@csrf_exempt
def register(request):
    if request.method == 'POST':
        isJR = is_json_request(request)
        signup_form = UserSignupForm(data=request.POST)

        if signup_form.is_valid():
            username = signup_form.clean_username()
            password = signup_form.clean_password2()
            user = signup_form.save()
            user_profile = UserProfile(user=user)
            user_profile.save()

            user = authenticate(username=username, password=password)

            login(request, user)
            if isJR:
                return HttpResponse(
                    json.dumps(user.get_profile().dictify({'sessionid': request.session.session_key})),
                    content_type='application/json')
            else:
                return HttpResponseRedirect('/')
        else:
            if isJR:
                for field in signup_form:
                    if len(field.errors) > 0:
                        return HttpResponseBadRequest(field.errors[0])
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
        isJR = is_json_request(request)
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            if isJR:
                return HttpResponse(
                    json.dumps(user.get_profile().dictify({'sessionid': request.session.session_key})),
                    content_type='application/json')
            else:
                return HttpResponseRedirect('/')
        else:
            if isJR:
                return HttpResponseNotFound('Invalid login')
            else:
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


@login_required
def get_teach_lessons(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound('User does not exist')

    lessons = Lesson.objects.filter(teacher=user)
    response = []
    for lesson in lessons:
        nregs = LessonReg.objects.filter(lesson=lesson).count()
        response.append(lesson.dictify({"nregs": nregs}))

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')


@login_required
def get_study_lessons(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound('User does not exist')

    lesson_regs = LessonReg.objects.filter(student=user)
    response = []
    for lesson_reg in lesson_regs:
        lesson = lesson_reg.lesson
        nregs = LessonReg.objects.filter(lesson=lesson).count()
        response.append(lesson.dictify({"nregs": nregs}))

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')


@login_required
def get_lesson_regs(request, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return HttpResponseNotFound('Lesson does not exist')

    if request.user.username not in (lesson.teacher.username, 'admin'):
        return HttpResponseForbidden('No permission to view registration details')

    lesson_regs = LessonReg.objects.filter(lesson__id=lesson_id)
    response = []
    for lesson_reg in lesson_regs:
        lesson_reg_logs = LessonRegLog.objects.filter(lesson_reg=lesson_reg)
        total = lesson_reg_logs.count()
        unused = lesson_reg_logs.filter(use_time=None).count()
        response.append(lesson_reg.dictify({"total": total, "unused": unused}))

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')


@login_required
def get_lesson_reg_logs(request, reg_id):
    try:
        lesson_reg = LessonReg.objects.get(id=reg_id)
    except LessonReg.DoesNotExist:
        return HttpResponseNotFound('Lesson registration does not exist')

    teacher = lesson_reg.lesson.teacher
    student = lesson_reg.student
    users_allowed = [teacher.username, 'admin']
    if student:
        users_allowed.append(student.username)
    if request.user.username not in users_allowed:
        return HttpResponseForbidden('No permission to view lesson registration logs')

    response = []
    lesson_reg_logs = LessonRegLog.objects.filter(lesson_reg=lesson_reg)
    for lesson_reg_log in lesson_reg_logs:
        response.append(lesson_reg_log.dictify())

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')

@login_required
@csrf_exempt
def lesson_messages(request):
    user = request.user
    if request.method == 'POST':
        data = json.loads(request.body)
        if 'create' in data:
            entry = data['create']
            try:
                lesson = Lesson.objects.get(id=entry['lesson_id'])
            except Lesson.DoesNotExist:
                return HttpResponseNotFound('Lesson does not exist')
            valid_usernames = [lesson.teacher.username, 'admin']
            for lesson_reg in LessonReg.objects.filter(lesson=lesson):
                if lesson_reg.student:
                    valid_usernames.append(lesson_reg.student.username)
            if user.username in valid_usernames:
                message = Message(lesson=lesson, sender=user, body=entry['body'])
                message.save()
            else:
                return HttpResponseForbidden('No permission to post message')

        elif 'delete' in data:
            qs = Message.objects.filter(id=data['delete']['message_id'])
            if qs.exists():
                if user.username in (qs.first().sender.username, 'admin'):
                    qs.delete()
                else:
                    return HttpResponseForbidden('No permission to delete message')
            else:
                return HttpResponseNotFound('Message does not exist')

        return HttpResponse(json.dumps({}),
                            content_type='application/json')

    else:
        lessons = Lesson.objects.filter(teacher=user)
        lessons = [lesson for lesson in lessons]
        for lesson_reg in LessonReg.objects.filter(student=user):
            if lesson_reg.lesson not in lessons:
                lessons.append(lesson_reg.lesson)
        messages = Message.objects.filter(lesson__in=lessons).order_by('-id')
        response = []
        for message in messages:
            response.append(message.dictify())

        return HttpResponse(json.dumps(response, cls=DateEncoder),
                            content_type='application/json')


@login_required
@csrf_exempt
def update_lesson(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if 'create' in data:
            lesson = Lesson(teacher=request.user, **data['create'])
            lesson.save()
        elif 'update' in data:
            entry = data['update']
            lesson_id = entry.pop('lesson_id')
            qs = Lesson.objects.filter(id=lesson_id)
            if qs.exists():
                if request.user.username in (qs.first().teacher.username, 'admin'):
                    qs.update(**entry)
                else:
                    return HttpResponseForbidden('No permission to update lesson')
            else:
                return HttpResponseNotFound('Lesson does not exist')
        elif 'delete' in data:
            lesson_id = data['delete']['lesson_id']
            qs = Lesson.objects.filter(id=lesson_id)
            if qs.exists():
                if request.user.username in (qs.first().teacher.username, 'admin'):
                    qs.delete()
                else:
                    return HttpResponseForbidden('No permission to delete lesson')
            else:
                return HttpResponseNotFound('Lesson does not exist')

        return HttpResponse(json.dumps({}),
                            content_type='application/json')
    else:
        return HttpResponseBadRequest('POST is required')


@login_required
@csrf_exempt
def update_lesson_reg_and_logs(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if 'create' in data:
            entry = data['create']
            try:
                lesson = Lesson.objects.get(id=entry['lesson_id'])
            except Lesson.DoesNotExist:
                return HttpResponseNotFound('Lesson does not exist')
            if request.user.username in (lesson.teacher.username, 'admin'):
                lesson_reg = LessonReg(lesson=lesson,
                                       student_first_name=entry['first_name'],
                                       student_last_name=entry['last_name'],
                                       data=entry['data'])
                lesson_reg.save()
            else:
                return HttpResponseForbidden('No permission to add new student')

        elif 'update' in data:
            entry = data['update']
            reg_id = entry.pop('reg_id')
            qs = LessonReg.objects.filter(id=reg_id)
            if qs.exists():
                lesson_reg = qs.first()
                if request.user.username in (lesson_reg.lesson.teacher.username, 'admin'):
                    rlogs = entry.pop('rlogs')
                    qs.update(**entry)
                    for log in rlogs['create']:
                        lesson_reg_log = LessonRegLog(lesson_reg=lesson_reg,
                                                      use_time=log['use_time'],
                                                      data=log['data'])
                        lesson_reg_log.save()
                    for log in rlogs['update']:
                        rlog_id = log.pop('rlog_id')
                        qs = LessonRegLog.objects.filter(id=rlog_id)
                        if qs.exists():
                            lesson_reg_log = qs.first()
                            if request.user.username in (lesson_reg_log.lesson_reg.lesson.teacher.username, 'admin'):
                                qs.update(**log)
                            else:
                                return HttpResponseForbidden('No permission to update lesson registration log')
                        else:
                            return HttpResponseNotFound('Lesson registration log does not exist')
                    for log in rlogs['delete']:
                        rlog_id = log.pop('rlog_id')
                        qs = LessonRegLog.objects.filter(id=rlog_id)
                        if qs.exists():
                            lesson_reg_log = qs.first()
                            if request.user.username in (lesson_reg_log.lesson_reg.lesson.teacher.username, 'admin'):
                                qs.delete()
                            else:
                                return HttpResponseForbidden('No permission to delete lesson registration log')
                        else:
                            return HttpResponseNotFound('Lesson registration log does not exist')

                else:
                    return HttpResponseForbidden('No permission to update lesson registration')
            else:
                return HttpResponseNotFound('Lesson registration does not exist')

        elif 'delete' in data:
            reg_id = data['delete']['reg_id']
            qs = LessonReg.objects.filter(id=reg_id)
            if qs.exists():
                if request.user.username in (qs.first().lesson.teacher.username, 'admin'):
                    qs.delete()
                else:
                    return HttpResponseForbidden('No permission to delete lesson registration')
            else:
                return HttpResponseNotFound('Lesson registration does not exist')

        return HttpResponse(json.dumps({}),
                            content_type='application/json')

    else:
        return HttpResponseBadRequest('POST is required')






@csrf_exempt
def debug_reset_db(request):
    if request.method == 'POST':
        User.objects.exclude(username='admin').delete()
        user = User(username='test', email='test@test.com', first_name='first', last_name='last')
        user.set_password('test')
        user.save()

        UserProfile.objects.all().delete()
        user_profile = UserProfile(user=user)
        user_profile.save()

        Lesson.objects.all().delete()
        lesson = Lesson(teacher=user,
                        name='Folk Guitar Basics',
                        description='An introductory lesson for people who want to pick up guitar fast with no '
                                    'previous experience')
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

        message = Message(lesson=lesson, sender=user,
                          body='Please bring your own guitar for the class')
        message.save()

        if is_json_request(request):
            return HttpResponse(json.dumps({}),
                                content_type='application/json')
        else:
            return HttpResponse('<p>DB Reset successful</p>')

    else:
        return HttpResponse(
            '<form method="post" action="/debug_reset_db/"><button type="submit">Reset DB</button><form>')

