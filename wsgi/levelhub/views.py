import json

import django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from forms import UserForm

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
    for key in sorted(request.META.keys()):
        print "%s =  %s" % (key, request.META[key])
    return render(request, 'home/home.html', {"version": django.VERSION})


@csrf_exempt
def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            registered = True

        else:
            print "user_form.errors", user_form.errors

    else:
        user_form = UserForm()

    return render(request,
                  'home/register.html',
                  {'user_form': user_form, 'registered': registered}
    )


@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return HttpResponseRedirect('/')
            #return HttpResponse(json.dumps({"user": str(user)}), content_type="application/json")
        else:
            return HttpResponse("Invalid login details")

    else:
        return render(request, 'home/login.html', {})


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')
