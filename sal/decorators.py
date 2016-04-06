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
    """Decorator for View subclasses to restrict by business unit."""
    if not isinstance(cls, type) or not issubclass(cls, View):
        raise Exception("Must be applied to subclass of View")

    def access_required(f):
        def decorator(*args, **kwargs):
            user = args[0].user
            if "bu_id" in kwargs:
                business_unit = get_object_or_404(
                    BusinessUnit, pk=kwargs['bu_id'])
            elif "group_id" in kwargs:
                business_unit = get_object_or_404(
                    MachineGroup, pk=kwargs["group_id"]).business_unit
            elif "machine_id" in kwargs:
                business_unit = get_object_or_404(
                    Machine,
                    pk=kwargs["machine_id"]).machine_group.business_unit
            else:
                business_unit = None

            if (not user.userprofile.level == "GA" and (not business_unit or
                business_unit not in user.businessunit_set.all())):
                raise PermissionDenied()
            else:
                return f(*args, **kwargs)
        return decorator

    access_decorator = method_decorator(access_required)
    cls.dispatch = access_decorator(cls.dispatch)
    return cls
