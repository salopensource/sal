# from json_response import *
# from server.models import *
# from django.core.exceptions import PermissionDenied
# import base64
#
# def validate_api_key(function):
#     def wrap(request, *args, **kwargs):
#         public_key = request.META.get('HTTP_PUBLICKEY', False)
#         private_key = request.META.get('HTTP_PRIVATEKEY', False)
#         try:
#             api_key = ApiKey.objects.get(private_key=private_key, public_key=public_key)
#         except ApiKey.DoesNotExist:
#             raise PermissionDenied()
#         return function(request, *args, **kwargs)
#     wrap.__doc__=function.__doc__
#     wrap.__name__=function.__name__
#     return wrap
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from server.models import *

class ApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        public_key = request.META.get('HTTP_PUBLICKEY', False)
        private_key = request.META.get('HTTP_PRIVATEKEY', False)
        if not public_key or not private_key:
            return None

        try:
            api_key = ApiKey.objects.get(private_key=private_key, public_key=public_key)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')

        return (api_key, None)

class HasRWPermission(permissions.BasePermission):
    """
    Only allows RW API keys to write
    """

    def has_object_permission(self, request, view, obj):
        public_key = request.META.get('HTTP_PUBLICKEY', False)
        private_key = request.META.get('HTTP_PRIVATEKEY', False)
        if not public_key or not private_key:
            return False

        try:
            api_key = ApiKey.objects.get(private_key=private_key, public_key=public_key)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to keys that have RW.
        return api_key.read_write
