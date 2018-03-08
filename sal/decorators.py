"""Decorators for class based views."""


import base64
import logging
from functools import wraps


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View

from server.models import BusinessUnit, Machine, MachineGroup, ProfileLevel


def class_login_required(cls):
    """Class decorator for View subclasses to restrict to logged in."""
    decorator = method_decorator(login_required)
    cls.dispatch = decorator(cls.dispatch)
    return cls


def class_ga_required(cls):
    """Class decorator for View subclasses to restrict to GA."""
    decorator = method_decorator(ga_required)
    cls.dispatch = decorator(cls.dispatch)
    return cls


def class_staff_required(cls):
    """Class decorator for View subclasses to restrict to staff."""
    decorator = method_decorator(staff_required)
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
        404 if requested group doesn't exist.
    """
    def access_required(function):
        def decorator(*args, **kwargs):
            # The request object is the first arg to a view
            request = args[0]
            user = request.user
            business_unit = cls.get_business_unit(**kwargs)

            if has_access(user, business_unit):
                return function(*args, **kwargs)
            else:
                raise PermissionDenied()
        return decorator

    access_decorator = method_decorator(access_required)
    cls.dispatch = access_decorator(cls.dispatch)
    return cls


def access_required(model):
    """Decorator for view functions to restrict by business unit.

    This decorator requires the view to have a parameter whose name
    ends with '_id'. If there is more than on parameter that meets that
    criteria, who knows what will happen!

    Args:
        model (BusinessUnit, MachineGroup, Machine): The model class
            that will be retrieved by URL parameter.

    Returns:
        Decorated view function.

    Raises:
        403 Pemission Denied if current user does not have access.
        404 if requested group doesn't exist.
    """

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            # The request object is the first arg to a view
            request = args[0]
            user = request.user
            instance, business_unit = get_business_unit_by(model, **kwargs)

            if has_access(user, business_unit):
                # Stash the business unit and instance to minimize
                # later DB queries.
                kwargs['business_unit'] = business_unit
                kwargs['instance'] = instance
                return function(*args, **kwargs)
            else:
                # Hide the 404 response from users without perms.
                raise PermissionDenied()

        return wrapper

    return decorator


def get_business_unit_by(model, **kwargs):
    try:
        pk = [v for k, v in kwargs.items() if k.endswith('_id')].pop()
    except IndexError:
        raise ValueError('View lacks an ID parameter!')

    try:
        instance = get_object_or_404(model, pk=pk)
    except ValueError:
        # Sal allows machine serials instead of machine ID in URLs.
        # Handle that special case.
        if model is Machine:
            instance = get_object_or_404(model, serial=pk)

    if isinstance(instance, MachineGroup):
        return (instance, instance.business_unit)
    elif isinstance(instance, Machine):
        return (instance, instance.machine_group.business_unit)
    else:
        return (instance, instance)


def is_global_admin(user):
    return user.userprofile.level == ProfileLevel.global_admin


def key_auth_required(function):

    @wraps(function)
    def wrap(request, *args, **kwargs):
        # Check for valid basic auth header
        if hasattr(settings, 'BASIC_AUTH'):
            use_auth = settings.BASIC_AUTH
        else:
            use_auth = True

        if use_auth is False:
            return view(request, *args, **kwargs)  # noqa: F821

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

    return wrap


def has_access(user, business_unit):
    if is_global_admin(user):
        return True

    if business_unit:
        return user.businessunit_set.filter(pk=business_unit.pk).exists()
    else:
        # Special case: If a user is in ALL business units, they don't
        # need GA.
        return user.businessunit_set.count() == BusinessUnit.objects.count()


def ga_required(function):
    """View decorator to redirect non GA users.

    Wrapped function must have the request object as the first argument.
    """
    # TODO: This can be removed once a class_required_level decoratir is created
    @wraps(function)
    def wrapper(*args, **kwargs):
        if args[0].user.userprofile.level != ProfileLevel.global_admin:
            return redirect(reverse('home'))
        else:
            return function(*args, **kwargs)

    return wrapper


def required_level(*decorator_args):
    """View decorator to redirect users without acceptable userprofile..

    Wrapped function must have the request object as the first argument.

    Args:
        *args (server.model.UserProfile.LEVEL_CHOICES) Any number of
            user profile level choices that should be permitted access.
    """

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):
            if args[0].user.userprofile.level not in decorator_args:
                return redirect(reverse('home'))
            else:
                return function(*args, **kwargs)

        return wrapper

    return decorator


def staff_required(function):
    """View decorator to redirect non staff users.

    Wrapped function must have the request object as the first argument.
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not args[0].user.is_staff:
            return redirect(reverse('home'))
        else:
            return function(*args, **kwargs)

    return wrapper


def handle_access(request, group_type, group_id):
    models = {
        'machine_group': MachineGroup,
        'business_unit': BusinessUnit,
        'machine': Machine}
    if group_type == 'all':
        business_unit = None
    else:
        _, business_unit = get_business_unit_by(models[group_type], group_id=group_id)

    if not has_access(request.user, business_unit):
        logging.warning("%s attempted to access %s for which they have no permissions.",
                        request.user, group_type)
        raise Http404
