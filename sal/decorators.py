"""Decorators for class based views."""


from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse

import base64

from server.models import BusinessUnit, Machine, MachineGroup


def class_login_required(cls):
    """Class decorator for View subclasses to restrict to logged in."""
    if not isinstance(cls, type) or not issubclass(cls, View):
        raise Exception("Must be applied to subclass of View")
    decorator = method_decorator(login_required)
    cls.dispatch = decorator(cls.dispatch)
    return cls


def class_access_required(cls):
    """Decorator for View subclasses to restrict by business unit.

    Class must declare a classmethod `get_business_unit` that returns
    the BusinessUnit object that applies to the query in question.

    Args:
        cls: Class to decorate.

    Returns:
        Decorated class.

    Raises:
        403 Pemission Denied if current user does not have access.
    """
    def access_required(f):
        def decorator(*args, **kwargs):
            user = args[0].user
            business_unit = cls.get_business_unit(**kwargs)

            if is_global_admin(user) or has_access(user, business_unit):
                return f(*args, **kwargs)
            else:
                raise PermissionDenied()
        return decorator

    access_decorator = method_decorator(access_required)
    cls.dispatch = access_decorator(cls.dispatch)
    return cls


def is_global_admin(user):
    return user.userprofile.level == "GA"

# def view_or_basicauth(view, request, *args, **kwargs):
#     # Check for valid basic auth header
#     if hasattr(settings, 'BASIC_AUTH'):
#         use_auth = settings.BASIC_AUTH
#     else:
#         use_auth = True
#
#     if use_auth == False:
#         return view(request, *args, **kwargs)
#
#     if 'HTTP_AUTHORIZATION' in request.META:
#         auth = request.META['HTTP_AUTHORIZATION'].split()
#         if len(auth) == 2:
#             if auth[0].lower() == "basic":
#                 uname, key = base64.b64decode(auth[1]).split(':')
#                 try:
#                     machine_group = MachineGroup.objects.get(key=key)
#                 except MachineGroup.DoesNotExist:
#                     machine_group = None
#
#                 if machine_group is not None and uname == 'sal':
#                     return view(request, *args, **kwargs)
#
#     # Either they did not provide an authorization header or
#     # something in the authorization attempt failed. Send a 401
#     # back to them to ask them to authenticate.
#     response = HttpResponse()
#     response.status_code = 401
#     response['WWW-Authenticate'] = 'Basic realm="%s"' % settings.BASIC_AUTH_REALM
#     return response
#
#
# def key_auth_required(view_func):
#     def wrapper(request, *args, **kwargs):
#         return view_or_basicauth(view_func, request, *args, **kwargs)
#     return wrapper(view_func)

def key_auth_required(function):
    def wrap(request, *args, **kwargs):
        # Check for valid basic auth header
        if hasattr(settings, 'BASIC_AUTH'):
            use_auth = settings.BASIC_AUTH
        else:
            use_auth = True

        if use_auth == False:
            return view(request, *args, **kwargs)

        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname, key = base64.b64decode(auth[1]).split(':')
                    try:
                        machine_group = MachineGroup.objects.get(key=key)
                    except MachineGroup.DoesNotExist:
                        machine_group = None

                    if machine_group is not None and uname == 'sal':
                        return function(request, *args, **kwargs)

        # Either they did not provide an authorization header or
        # something in the authorization attempt failed. Send a 401
        # back to them to ask them to authenticate.
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm=Sal'
        return response
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def has_access(user, business_unit):
    return (business_unit and
            business_unit in user.businessunit_set.all())
