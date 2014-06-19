import django
from django.shortcuts import render_to_response

def home(request):
    return render_to_response(request, 'home/home.html', {"version": django.VERSION})
