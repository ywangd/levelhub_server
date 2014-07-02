from itertools import chain, groupby
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
from django.db.models import Q

from levelhub.forms import UserSignupForm, UserForm
from levelhub.models import UserProfile, Lesson, LessonReg, LessonRegLog, Message, LessonMessage, UserMessage
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


def query_user_lessons(user):
    teach_lessons = [lesson for lesson in Lesson.objects.filter(teacher=user)]
    study_lessons = [lesson_reg.lesson for lesson_reg in LessonReg.objects.filter(student=user)]
    return (teach_lessons, study_lessons)


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
        response.append(lesson.dictify({'nregs': nregs}))

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')


@login_required
def get_study_lessons(request):
    # Can only view one's own studies
    lesson_regs = LessonReg.objects.filter(student=request.user)
    response = []
    for lesson_reg in lesson_regs:
        lesson = lesson_reg.lesson
        nregs = LessonReg.objects.filter(lesson=lesson).count()
        response.append(lesson.dictify({'nregs': nregs}))

    return HttpResponse(json.dumps(response, cls=DateEncoder),
                        content_type='application/json')


@login_required
def get_user_lessons(request):
    teach_lessons, study_lessons = query_user_lessons(request.user)
    response = {'teach': [], 'study': []}
    for lesson in teach_lessons:
        nregs = LessonReg.objects.filter(lesson=lesson).count()
        response['teach'].append(lesson.dictify({'nregs': nregs}))

    for lesson in study_lessons:
        nregs = LessonReg.objects.filter(lesson=lesson).count()
        response['study'].append(lesson.dictify({'nregs': nregs}))

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

    # Sort student alphabetically
    response.sort(key=lambda x: x['student']['display_name'] if x['student'] else ' '.join(
        [x['student_first_name'], x['student_last_name']]))

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
def user_search(request):
    phrase = request.GET['phrase']
    users = User.objects.filter(Q(username__contains=phrase)
                        | Q(first_name__contains=phrase)
                        | Q(last_name__contains=phrase)).exclude(username='admin').exclude(username=request.user.username)
    response = []
    for user in users:
        response.append(user.get_profile().dictify())

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
            message = Message(sender=user, body=entry['body'])
            message.save()
            lms = []
            for lesson_id in entry['lesson_ids']:
                try:
                    lesson = Lesson.objects.get(id=lesson_id)
                except Lesson.DoesNotExist:
                    message.delete()
                    return HttpResponseNotFound('Lesson does not exist')
                valid_usernames = [lesson.teacher.username, 'admin']
                for lesson_reg in LessonReg.objects.filter(lesson=lesson):
                    if lesson_reg.student:
                        valid_usernames.append(lesson_reg.student.username)
                if user.username in valid_usernames:
                    lms.append(LessonMessage(lesson=lesson, message=message))
                else:
                    message.delete()
                    return HttpResponseForbidden('No permission to post message')

            LessonMessage.objects.bulk_create(lms)

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
        teach_lessons, study_lessons = query_user_lessons(user)

        lms = LessonMessage.objects.filter(
            lesson__in=[lesson for lesson in chain(teach_lessons, study_lessons)]).order_by('message')

        response = []
        for msg, lsn in groupby(lms, key=lambda x: x.message):
            response.append({'message': msg.dictify(), 'lessons': [x.lesson.dictify() for x in list(lsn)]})

        response.sort(key=lambda x: -x['message']['message_id'])

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
                if 'student_id' in entry:
                    try:
                        student = User.objects.get(id=entry['student_id'])
                    except User.DoesNotExist:
                        return HttpResponseNotFound('User does not exist')
                    try:  # avoid duplicate enrollment
                        LessonReg.objects.get(lesson=lesson, student=student)
                        return HttpResponseBadRequest("User is already enrolled")
                    except LessonReg.DoesNotExist:
                        pass
                    lesson_reg = LessonReg(lesson=lesson,
                                           student=student,
                                           student_first_name=student.first_name,
                                           student_last_name=student.last_name,
                                           data=entry['data'])
                else:
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
        elsa = User(username='elsa', email='elsa@frozen.com', first_name='Queen', last_name='Elsa')
        elsa.set_password('test')
        elsa.save()

        anna = User(username='anna', email='anna@frozen.com', first_name='Princess', last_name='Anna')
        anna.set_password('test')
        anna.save()

        chris = User(username='chris', first_name='Christof', last_name='Iceminer')
        chris.set_password('test')
        chris.save()

        troll = User(username='troll', first_name='Mountain', last_name='Troll')
        troll.set_password('test')
        troll.save()

        olaf = User(username='olaf', email='olaf@fronzen.com')
        olaf.set_password('test')
        olaf.save()

        UserProfile.objects.all().delete()
        user_profile = UserProfile(user=elsa)
        user_profile.save()
        user_profile = UserProfile(user=anna)
        user_profile.save()
        user_profile = UserProfile(user=olaf)
        user_profile.save()
        user_profile = UserProfile(user=troll)
        user_profile.save()
        user_profile = UserProfile(user=chris)
        user_profile.save()

        Lesson.objects.all().delete()
        magic_lesson = Lesson(teacher=elsa,
                              name='Cool Magic Basics',
                              description='An introductory lesson for people who want to learn cool magic fast with no '
                                          'previous experience')
        magic_lesson.save()

        love_lesson = Lesson(teacher=olaf,
                             name='Practical Love Advice',
                             description='You can be as lazy as you like, yet Love is still guaranteed. Yes it is '
                                         'realistic if you join now.')
        love_lesson.save()

        medic_lesson = Lesson(teacher=troll,
                              name='Expert Medical Tricks',
                              description='Got a brain damage or wanna cure one? Join now and you will learn in no time')
        medic_lesson.save()

        LessonReg.objects.all().delete()
        lesson_reg_1 = LessonReg(lesson=magic_lesson,
                                 student_first_name='Prince',
                                 student_last_name='Hans')
        lesson_reg_1.save()
        lesson_reg_2 = LessonReg(lesson=magic_lesson,
                                 student_first_name='Snow',
                                 student_last_name='Giant')
        lesson_reg_2.save()

        lesson_reg_3 = LessonReg(lesson=magic_lesson, student=anna)
        lesson_reg_3.save()

        LessonReg(lesson=love_lesson, student=elsa).save()

        LessonRegLog.objects.all().delete()
        lesson_reg_logs_1 = [LessonRegLog(lesson_reg=lesson_reg_1,
                                          use_time='2014-06-22 15:30:00' if i < 14 else None) for i in range(25)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_1)
        lesson_reg_logs_2 = [LessonRegLog(lesson_reg=lesson_reg_2,
                                          use_time='2014-06-22 15:30:00' if i < 3 else None) for i in range(5)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_2)

        message = Message(sender=elsa,
                          body='Please bring your own winter coat to the class. Renting program is no longer '
                               'available.',
                          creation_time='2014-06-22 15:30:00Z')
        message.save()
        lesson_message = LessonMessage(lesson=magic_lesson, message=message)
        lesson_message.save()

        message = Message(sender=anna,
                          body='I love this lesson. Definitely going to recommend to my friends.')
        message.save()
        lesson_message = LessonMessage(lesson=magic_lesson, message=message)
        lesson_message.save()
        lesson_message = LessonMessage(lesson=love_lesson, message=message)
        lesson_message.save()

        if is_json_request(request):
            return HttpResponse(json.dumps({}),
                                content_type='application/json')
        else:
            return HttpResponse('<p>DB Reset successful</p>')

    else:
        return HttpResponse(
            '<form method="post" action="/debug_reset_db/"><button type="submit">Reset DB</button><form>')

