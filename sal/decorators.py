"""Decorators for class based views."""


from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View

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


def has_access(user, business_unit):
    return (business_unit and
            business_unit in user.businessunit_set.all())
