import json

import django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from forms import UserForm

def is_json_request(request):
    if "json" in request.POST or "json" in request.GET:
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
    jq = is_json_request(request)
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            if jq:
                return HttpResponse(json.dumps({"user": str(user),
                                                "sessionid": request.session.session_key}),
                                    content_type="application/json")
            else:
                return HttpResponseRedirect('/')
        else:
            if jq:
                return HttpResponse(json.dumps({"err": "Invalid login"}),
                                    content_type="application/json")

            return HttpResponse("Invalid login")

    else:
        return render(request, 'home/login.html', {})


@login_required
@csrf_exempt
def user_logout(request):
    print "logging out ..."
    logout(request)
    if is_json_request(request):
        return HttpResponse(json.dumps({}),
                            content_type="application/json")
    else:
        return HttpResponseRedirect('/')
