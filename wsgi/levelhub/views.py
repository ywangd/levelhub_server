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
from levelhub.models import UserProfile, Lesson, LessonReg, LessonRegLog, Message, LessonMessage, UserMessage, \
    LessonRequest
from levelhub.utils import DateEncoder
from levelhub.consts import *


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


# ############################################################################
# Helper functions
#############################################################################

# package the information as json and return to user
# Always add pulse for each request. A pulse carries small size notification
# information, such as number of new requests. So a notification can be displayed
# at user side.
def pack_json_response(request, d, add_pulse=True):
    if add_pulse:
        j = json.dumps({'pulse': {'n_new_requests': peek_lesson_requests(request.user)},
                        'main': d},
                       cls=DateEncoder)
    else:
        j = json.dumps(d)
    return HttpResponse(j, content_type='application/json')


def user_get(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def lesson_get(lesson_id):
    try:
        return Lesson.objects.get(id=lesson_id, status=LESSON_ACTIVE)
    except Lesson.DoesNotExist:
        return None


def lesson_reg_get(**kwargs):
    try:
        return LessonReg.objects.get(status=LESSON_REG_ACTIVE, **kwargs)
    except LessonReg.DoesNotExist:
        return None


def lesson_reg_log_get(**kwargs):
    try:
        a = LessonRegLog.objects.get(**kwargs)
        return a
    except LessonRegLog.DoesNotExist:
        return None


def lesson_request_get(**kwargs):
    try:
        return LessonRequest.objects.get(**kwargs)
    except LessonRequest.DoesNotExist:
        return None


def message_get(message_id):
    try:
        return Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return None


def role_of_lesson(user, lesson):
    if user.username in [lesson.teacher.username, 'admin']:
        return ROLE_LESSON_MANAGER
    elif lesson_reg_get(lesson=lesson, student=user):
        return ROLE_LESSON_STUDENT
    else:
        return ROLE_LESSON_NONE


# Peek the lesson requests without changing their status
def peek_lesson_requests(user):
    # As receiver
    incoming_requests = LessonRequest.objects.filter(
        receiver=user, is_new=True, status__in=REQUEST_RECEIVER_NOTICE)
    # As sender
    outgoing_requests = LessonRequest.objects.filter(
        sender=user, is_new=True, status__in=REQUEST_SENDER_NOTICE)

    return incoming_requests.count() + outgoing_requests.count()


# Get the lessons an user teaches. Anyone can view an user's teaches
def query_teach_lessons(user):
    lessons = Lesson.objects.filter(teacher=user, status=LESSON_ACTIVE)
    response = []
    for lesson in lessons:
        nregs = LessonReg.objects.filter(lesson=lesson, status=LESSON_REG_ACTIVE).count()
        response.append(lesson.dictify({'nregs': nregs}))
    return response


# study lesson is different than teach lesson in that it contains a
# sub-element pointing to the registration
# Can only view one's own studies
def query_study_lessons(user):
    lesson_regs = LessonReg.objects.filter(student=user, status=LESSON_REG_ACTIVE)
    response = []
    for lesson_reg in lesson_regs:
        lesson = lesson_reg.lesson
        nregs = LessonReg.objects.filter(lesson=lesson, status=LESSON_REG_ACTIVE).count()
        d = lesson.dictify({'nregs': nregs})
        lesson_reg_logs = LessonRegLog.objects.filter(lesson_reg=lesson_reg)
        d['registration'] = {
            'reg_id': lesson_reg.id,
            'status': lesson_reg.status,
            'creation_time': lesson_reg.creation_time,
            'daytimes': lesson_reg.daytimes,
            'data': lesson_reg.data,
            'total': lesson_reg_logs.count(),
            'unused': lesson_reg_logs.filter(use_time=None).count(),
        }
        response.append(d)
    return response


#############################################################################
# Views
#############################################################################
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
                return pack_json_response(request,
                                          user.get_profile().dictify(
                                              {'sessionid': request.session.session_key}))
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
                return pack_json_response(request,
                                          user.get_profile().dictify(
                                              {'sessionid': request.session.session_key}))
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
    logout(request)
    if is_json_request(request):
        return pack_json_response(request, {}, add_pulse=False)
    else:
        return HttpResponseRedirect('/')


@login_required
def user_search(request):
    phrase = request.GET['phrase']
    users = User.objects.filter(Q(username__contains=phrase)
                                | Q(first_name__contains=phrase)
                                | Q(last_name__contains=phrase)
                                & ~Q(username='admin')
                                & ~Q(username=request.user.username))
    response = []
    for user in users:
        response.append(user.get_profile().dictify())

    return pack_json_response(request, response)


@login_required
def lesson_search(request):
    phrase = request.GET['phrase']
    lessons = Lesson.objects.filter(Q(name__contains=phrase)
                                    | Q(description__contains=phrase)
                                    & Q(status=LESSON_ACTIVE))
    response = []
    for lesson in lessons:
        nregs = LessonReg.objects.filter(lesson=lesson, status=LESSON_REG_ACTIVE).count()
        response.append(lesson.dictify({'nregs': nregs}))

    return pack_json_response(request, response)


# POST to create, update or delete a lesson
# GET to retrieve all teach and study lessons for the requesting user
@login_required
@csrf_exempt
def process_lessons(request):
    user = request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        action = data['action']

        if 'create' == action:
            Lesson(teacher=user, name=data['name'], description=data['description']).save()

        elif 'update' == action:
            lesson = lesson_get(data['lesson_id'])
            if not lesson:
                return HttpResponseNotFound('Lesson does not exist')
            role = role_of_lesson(user, lesson)
            if role != ROLE_LESSON_MANAGER:
                return HttpResponseForbidden('No permission to update lesson')
            lesson.name = data['name']
            lesson.description = data['description']
            lesson.save()

        elif 'delete' == action:
            lesson = lesson_get(data['lesson_id'])
            if not lesson:
                return HttpResponseNotFound('Lesson does not exist')
            role = role_of_lesson(user, lesson)
            if role != ROLE_LESSON_MANAGER:
                return HttpResponseForbidden('No permission to update lesson')
            lesson.delete()

        else:
            return HttpResponseBadRequest('Invalid action')

        return HttpResponse(json.dumps({}),
                            content_type='application/json')

    else:  # get teach and study lessons for the requesting user
        lesson_category = request.GET['category']

        if lesson_category == 'all':
            return pack_json_response(request, {'teach': query_teach_lessons(user),
                                                'study': query_study_lessons(user)})

        elif lesson_category == 'teach':
            # If a user_id is specified, use the user_id, otherwise use
            # requesting user
            if 'user_id' in request.GET and request.GET['user_id']:
                user = user_get(request.GET['user_id'])
                if not user:
                    return HttpResponseNotFound('User does not exist')
            return pack_json_response(request, query_teach_lessons(user))

        elif lesson_category == 'study':
            return pack_json_response(request, query_study_lessons(request.user))

        else:
            return HttpResponseBadRequest('Invalid lesson category')


# POST to action on a single request
# GET to retrieve all requests for the requesting user
@login_required
@csrf_exempt
def process_lesson_requests(request):
    user = request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        action = data['action']

        if 'enroll' == action:

            lesson = lesson_get(data['lesson_id'])
            if not lesson:
                return HttpResponseNotFound('Lesson does not exist')

            if role_of_lesson(user, lesson) != ROLE_LESSON_MANAGER:
                return HttpResponseForbidden('No permission to enroll student')

            if 'student_id' in data:  # member enroll
                student = user_get(data['student_id'])
                if not student:
                    return HttpResponseNotFound('User does not exist')

                if lesson_reg_get(lesson=lesson, student=student):
                    return HttpResponseBadRequest('User is already enrolled')

                if lesson_request_get(sender=user, receiver=student, lesson=lesson):
                    return HttpResponseBadRequest('Duplicate request')

                LessonRequest(sender=user,
                              receiver=student,
                              lesson=lesson,
                              message=data['message'],
                              daytimes=data['daytimes'],
                              status=REQUEST_ENROLL,
                              is_new=True).save()

            else:  # non-member enroll
                LessonReg(lesson=lesson,
                          student_first_name=data['first_name'],
                          student_last_name=data['last_name'],
                          daytimes=data['daytimes']).save()

        elif 'join' == action:

            lesson = lesson_get(data['lesson_id'])
            if not lesson:
                return HttpResponseNotFound('Lesson does not exist')

            if lesson_reg_get(lesson=lesson, student=user):
                return HttpResponseBadRequest('You already joined')

            teacher = lesson.teacher

            if lesson_request_get(sender=user, receiver=teacher, lesson=lesson):
                return HttpResponseBadRequest('Duplicate request')

            if user.username == teacher.username:
                return HttpResponseBadRequest('You are teacher of the lesson')

            LessonRequest(sender=user,
                          receiver=teacher,
                          lesson=lesson,
                          message=data['message'],
                          status=REQUEST_JOIN,
                          is_new=True).save()

        elif 'deroll' == action:

            lesson_reg = lesson_reg_get(id=data['reg_id'])
            if not lesson_reg:
                return HttpResponseNotFound('Lesson registration does not exist')

            if role_of_lesson(user, lesson_reg.lesson) != ROLE_LESSON_MANAGER:
                return HttpResponseForbidden('No permission to disenroll student')

            if lesson_reg.student:  # Create notice for members
                LessonRequest(sender=user,
                              receiver=lesson_reg.student,
                              lesson=lesson_reg.lesson,
                              status=REQUEST_DEROLL,
                              is_new=True).save()
            # This request is a notice only, i.e. the receiver only gets to dismiss the
            # message without the options for accept or reject
            lesson_reg.status = LESSON_REG_DEROLL
            lesson_reg.save()

        elif 'quit' == action:

            lesson_reg = lesson_reg_get(id=data['reg_id'])
            if not lesson_reg:
                return HttpResponseNotFound('Lesson registration does not exist')

            if user.username != lesson_reg.student.username:
                return HttpResponseForbidden('No permission to quit the lesson registration')

            teacher = lesson_reg.lesson.teacher

            LessonRequest(sender=user,
                          receiver=teacher,
                          lesson=lesson_reg.lesson,
                          status=REQUEST_QUIT,
                          is_new=True).save()
            # This is also a notice only
            lesson_reg.status = LESSON_REG_QUIT
            lesson_reg.save()

        elif 'accept' == action or 'reject' == action:

            lesson_request = lesson_request_get(id=data['req_id'])
            if not lesson_request:
                return HttpResponseNotFound('Request does not exist')

            if user.username != lesson_request.receiver.username:
                return HttpResponseForbidden('No permission to accept request')

            if lesson_request.status not in REQUEST_ACCEPT_OR_REJECT:
                return HttpResponseBadRequest('The request can only be dismissed')

            if lesson_request.status == REQUEST_ENROLL:
                if action == 'accept':
                    lesson_request.status = REQUEST_ENROLL_ACCEPTED
                    LessonReg(lesson=lesson_request.lesson,
                              student=lesson_request.receiver,
                              daytimes=lesson_request.daytimes).save()
                else:
                    lesson_request.status = REQUEST_ENROLL_REJECTED
            elif lesson_request.status == REQUEST_JOIN:
                if action == 'accept':
                    lesson_request.status = REQUEST_JOIN_ACCEPTED
                    LessonReg(lesson=lesson_request.lesson,
                              student=lesson_request.sender).save()
                else:
                    lesson_request.status = REQUEST_JOIN_REJECTED
            else:
                return HttpResponseBadRequest('Invalid request status')

            lesson_request.is_new = True
            lesson_request.save()

        elif 'dismiss' == action:

            lesson_request = lesson_request_get(id=data['req_id'])
            if not lesson_request:
                return HttpResponseNotFound('Request does not exist')

            if (lesson_request.status in REQUEST_SENDER_DISMISS
                and user.username == lesson_request.sender.username) \
                    or (lesson_request.status in REQUEST_RECEIVER_DISMISS
                        and user.username == lesson_request.receiver.username):
                lesson_request.delete()
            else:
                return HttpResponseForbidden('No permission to dismiss the request')

        else:
            return HttpResponseBadRequest('Invalid action')

        return pack_json_response(request, {})

    else:  # method is GET
        # As receiver
        all_requests = LessonRequest.objects.filter(
            (Q(receiver=user) & Q(status__in=REQUEST_RECEIVER_VIEWABLE))
            | (Q(sender=user) & Q(status__in=REQUEST_SENDER_VIEWABLE))).order_by("-id")
        # Mark requests as read exclude those sent by the user as requests to enroll or join
        all_requests.filter(is_new=True).exclude(sender=user, status__in=[REQUEST_ENROLL, REQUEST_JOIN]).update(is_new=False)
        response = [req.dictify() for req in all_requests]
        return pack_json_response(request, response)


# Get all registration of a lesson or update one lesson registration
# Note that the creation and deletion of lesson registration are not handled here.
# Creation and deletion are handled by process_lesson_request.
@login_required
@csrf_exempt
def process_lesson_regs(request):
    user = request.user

    if request.method == 'POST':  # update a lesson registration
        data = json.loads(request.body)

        lesson_reg = lesson_reg_get(id=data['reg_id'])
        if not lesson_reg:
            return HttpResponseNotFound('Lesson registration does not exist')

        if role_of_lesson(user, lesson_reg.lesson) != ROLE_LESSON_MANAGER:
            return HttpResponseForbidden('No permission to modify the lesson registration')

        lesson_reg.daytimes = data['daytimes']
        if 'data' in data:
            lesson_reg.data = data['data']
        lesson_reg.save()
        return pack_json_response(request, {})

    else:  # method is GET
        lesson = lesson_get(request.GET['lesson_id'])
        if not lesson:
            return HttpResponseNotFound('Lesson does not exist')

        role = role_of_lesson(user, lesson)
        if role == ROLE_LESSON_NONE:
            return HttpResponseForbidden('No permission view registrations of the lesson')

        response = []
        for lesson_reg in LessonReg.objects.filter(lesson=lesson, status=LESSON_REG_ACTIVE):
            # Lesson registrations can be viewed by student with less information
            info_for_manager = None
            if role == ROLE_LESSON_MANAGER:
                lesson_reg_logs = LessonRegLog.objects.filter(lesson_reg=lesson_reg)
                total = lesson_reg_logs.count()
                unused = lesson_reg_logs.filter(use_time=None).count()
                info_for_manager = {'total': total, 'unused': unused}
            response.append(lesson_reg.dictify(info_for_manager))

        # sort student alphabetically
        response.sort(key=lambda x: x['student']['display_name'].lower() if x['student'] else ' '.join(
            [x['student_first_name'], x['student_last_name']]).lower())

        return pack_json_response(request, response)


# GET all reg logs for the given registration
# POST to create, update and delete reg logs for registration
@login_required
@csrf_exempt
def process_lesson_reg_logs(request):
    user = request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        for log in data:
            if log['action'] == 'create':
                lesson_reg = lesson_reg_get(id=log['reg_id'])
                if not lesson_reg:
                    return HttpResponseNotFound('Lesson registration does not exist')
                if role_of_lesson(user, lesson_reg.lesson) != ROLE_LESSON_MANAGER:
                    return HttpResponseForbidden('No permission to create lesson registration log')
                LessonRegLog(lesson_reg=lesson_reg,
                             use_time=log['use_time'],
                             data=log['data']).save()
            elif log['action'] == 'update':
                lesson_reg_log = lesson_reg_log_get(id=log['rlog_id'])
                if not lesson_reg_log:
                    return HttpResponseNotFound('Lesson registration log does not exist')
                if role_of_lesson(user, lesson_reg_log.lesson_reg.lesson) != ROLE_LESSON_MANAGER:
                    return HttpResponseForbidden('No permission to update lesson registration log')
                lesson_reg_log.use_time = log['use_time']
                lesson_reg_log.data = log['data']
                lesson_reg_log.save()
            elif log['action'] == 'delete':
                lesson_reg_log = lesson_reg_log_get(id=log['rlog_id'])
                if not lesson_reg_log:
                    return HttpResponseNotFound('Lesson registration log does not exist')
                if role_of_lesson(user, lesson_reg_log.lesson_reg.lesson) != ROLE_LESSON_MANAGER:
                    return HttpResponseForbidden('No permission to update lesson registration log')
                lesson_reg_log.delete()
            else:
                return HttpResponseBadRequest('Invalid action')

        return pack_json_response(request, {})

    else:  # method is GET
        lesson_reg = lesson_reg_get(id=request.GET['reg_id'])
        if not lesson_reg:
            return HttpResponseNotFound('Lesson registration does not exist')

        if role_of_lesson(user, lesson_reg.lesson) == ROLE_LESSON_MANAGER \
                or (lesson_reg.student and user.username == lesson_reg.student.username):
            response = [lesson_reg_log.dictify() for lesson_reg_log
                        in LessonRegLog.objects.filter(lesson_reg=lesson_reg).order_by('id')]
            return pack_json_response(request, response)
        else:
            return HttpResponseForbidden('No permission to view lesson registration logs')


@login_required
@csrf_exempt
def process_lesson_messages(request):
    user = request.user

    if request.method == 'POST':
        data = json.loads(request.body)
        action = data['action']

        if 'create' == action:

            lessons = []
            for lesson_id in data['lesson_ids']:
                lesson = lesson_get(lesson_id)
                if not lesson:
                    return HttpResponseNotFound('Lesson does not exist')

                role = role_of_lesson(user, lesson)
                if role == ROLE_LESSON_NONE:
                    return HttpResponseForbidden('No permission to post message')

                lessons.append(lesson)

            message = Message(sender=user, body=data['body'])
            message.save()
            LessonMessage.objects.bulk_create([LessonMessage(lesson=lesson, message=message)
                                               for lesson in lessons])

        elif 'delete' == action:
            message = message_get(data['message_id'])
            if not message:
                return HttpResponseNotFound('Message does not exist')
            if user.username not in [message.sender.username, 'admin']:
                return HttpResponseForbidden('No permission to delete message')
            message.delete()  # Any entries in LessonMessages are deleted as well by cascade

        else:
            return HttpResponseBadRequest('Invalid action')

        return pack_json_response(request, {})

    else:  # method is GET
        teach_lessons = [lesson for lesson in Lesson.objects.filter(teacher=user, status=LESSON_ACTIVE)]
        study_lessons = [lesson_reg.lesson for lesson_reg in
                         LessonReg.objects.filter(student=user, status=LESSON_REG_ACTIVE)]

        lesson_messages = LessonMessage.objects.filter(
            lesson__in=[lesson for lesson in chain(teach_lessons, study_lessons)]).order_by('message')

        # Find all lessons the message is sent to and group the display of lessons
        response = []
        for message, lesson in groupby(lesson_messages, key=lambda lm: lm.message):
            response.append({'message': message.dictify(),
                             'lessons': [x.lesson.dictify() for x in list(lesson)]})

        # Sort the final response by decreasing order of message id
        response.sort(key=lambda entry: -entry['message']['message_id'])

        return pack_json_response(request, response)


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

        chris = User(username='kris', first_name='Kristoff', last_name='Iceminer')
        chris.set_password('test')
        chris.save()

        troll = User(username='troll', first_name='Mountain', last_name='Troll')
        troll.set_password('test')
        troll.save()

        olaf = User(username='olaf', email='olaf@fronzen.com')
        olaf.set_password('test')
        olaf.save()

        hans = User(username='hans', email='hans@fronzen.com', first_name='Prince', last_name='Hans')
        hans.set_password('test')
        hans.save()

        UserProfile.objects.all().delete()
        user_profile = UserProfile(user=elsa,
                                   about="Let it go. Let it go. Can't hold back anymore. Let it go. Let it go. Turn "
                                         "away and slam the door. I don't care what they are going to say. Let the "
                                         "storm rage on. Cold never bothered me anyway.")
        user_profile.save()
        user_profile = UserProfile(user=anna,
                                   about="I grow up in a castle. My sister and me use to be very close when we were "
                                         "little. But one day she just shut me out and I never know why.")
        user_profile.save()
        user_profile = UserProfile(user=olaf)
        user_profile.save()
        user_profile = UserProfile(user=troll)
        user_profile.save()
        user_profile = UserProfile(user=chris)
        user_profile.save()
        UserProfile(user=hans).save()

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
                              description='Got a brain damage or wanna cure one? Join now and you will learn in no '
                                          'time.')
        medic_lesson.save()

        LessonRequest(sender=olaf, receiver=elsa, lesson=magic_lesson,
                      message='Cold and hot are both extreme. Putting them together just makes sense. I will finally '
                              'be a happy snowman in summer!',
                      status=REQUEST_JOIN).save()

        LessonRequest(sender=elsa, receiver=troll, lesson=medic_lesson,
                      message='I wanna learn how to cure a frozen heart',
                      status=REQUEST_JOIN).save()

        LessonReg.objects.all().delete()
        lesson_reg_1 = LessonReg(lesson=magic_lesson, student=hans)
        lesson_reg_1.save()
        lesson_reg_2 = LessonReg(lesson=magic_lesson,
                                 student_first_name='Marshmallow',
                                 student_last_name='Giant')
        lesson_reg_2.save()

        lesson_reg_3 = LessonReg(lesson=magic_lesson, student=anna)
        lesson_reg_3.save()

        lesson_reg_4 = LessonReg(lesson=love_lesson, student=elsa)
        lesson_reg_4.save()

        LessonRegLog.objects.all().delete()
        lesson_reg_logs_1 = [LessonRegLog(lesson_reg=lesson_reg_1,
                                          use_time='2014-06-22 15:30:00' if i < 14 else None) for i in range(25)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_1)
        lesson_reg_logs_2 = [LessonRegLog(lesson_reg=lesson_reg_2,
                                          use_time='2014-06-22 15:30:00' if i < 3 else None) for i in range(5)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs_2)

        lesson_reg_logs = [LessonRegLog(lesson_reg=lesson_reg_4,
                                        use_time='2014-07-01 16:30:00' if i < 8 else None) for i in range(18)]
        LessonRegLog.objects.bulk_create(lesson_reg_logs)

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

