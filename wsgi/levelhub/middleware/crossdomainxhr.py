import re

from django.utils.text import compress_string
from django.utils.cache import patch_vary_headers

from django import http

try:
    import levelhub.settings as settings

    XS_SHARING_ALLOWED_ORIGINS = settings.XS_SHARING_ALLOWED_ORIGINS
    XS_SHARING_ALLOWED_METHODS = settings.XS_SHARING_ALLOWED_METHODS
except:
    XS_SHARING_ALLOWED_ORIGINS = '*'
    XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']


class XsSharing(object):
    """
        This middleware allows cross-domain XHR using the html5 postMessage API.
         

        Access-Control-Allow-Origin: http://foo.example
        Access-Control-Allow-Methods: POST, GET, OPTIONS, PUT, DELETE
    """

    def process_request(self, request):

        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
        elif 'HTTP_X_CLIENT_IP' in request.META:
            origin = request.META['HTTP_X_CLIENT_IP']
        else:
            origin = request.META['HTTP_HOST']

        print "request headers: ", request.META["ACCESS_CONTROL_REQUEST_HEADERS"]

        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = http.HttpResponse()
            response['Access-Control-Allow-Origin'] = origin  # XS_SHARING_ALLOWED_ORIGINS
            response['Access-Control-Allow-Methods'] = ",".join(XS_SHARING_ALLOWED_METHODS)
            response['Access-Control-Allow-Credentials'] = 'true'

            return response

        return None

    def process_response(self, request, response):

        if "Access-Control-Allow-Headers" in response['Access-Control-Allow-Headers']:
            print "allow headers: ", response['Access-Control-Allow-Headers']
        else:
            print "NO allow headers"
            response['Access-Control-Allow-Headers'] = request.META["ACCESS_CONTROL_REQUEST_HEADERS"]

        # Avoid unnecessary work
        if response.has_header('Access-Control-Allow-Origin'):
            return response

        if 'HTTP_ORIGIN' in request.META:
            origin = request.META['HTTP_ORIGIN']
        elif 'HTTP_X_CLIENT_IP' in request.META:
            origin = request.META['HTTP_X_CLIENT_IP']
        else:
            origin = request.META['HTTP_HOST']

        response['Access-Control-Allow-Origin'] = origin  # XS_SHARING_ALLOWED_ORIGINS
        response['Access-Control-Allow-Methods'] = ",".join(XS_SHARING_ALLOWED_METHODS)
        response['Access-Control-Allow-Credentials'] = 'true'

        return response