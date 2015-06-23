from json_response import *
from server.models import *
from django.core.exceptions import PermissionDenied
import base64

def validate_api_key(function):
    def wrap(request, *args, **kwargs):
        public_key = request.META.get('HTTP_PUBLICKEY', False)
        private_key = request.META.get('HTTP_PRIVATEKEY', False)
        try:
            api_key = ApiKey.objects.get(private_key=private_key, public_key=public_key)
        except ApiKey.DoesNotExist:
            raise PermissionDenied()
        return function(request, *args, **kwargs)
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap
