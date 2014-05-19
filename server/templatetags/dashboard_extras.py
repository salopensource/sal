from django import template
from django.shortcuts import get_object_or_404
from server.models import *
from datetime import datetime
import dateutil.parser
from django.template.defaultfilters import date
from django.utils.timezone import utc
import pytz
from django.conf import settings

register = template.Library()

@register.filter
def humanreadablesize(kbytes):
    """Returns sizes in human-readable units. Input is kbytes"""
    try:
        kbytes = float(kbytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return "unknown"

    units = [(" KB", 2**10), (" MB", 2**20), (" GB", 2**30), (" TB", 2**40)]
    for suffix, limit in units:
        if kbytes > limit:
            continue
        else:
            return str(round(kbytes/float(limit/2**10), 1)) + suffix
humanreadablesize.is_safe = True

@register.filter
def bu_machine_count(bu_id):
    """Returns the number of machines contained within the child Machine Groups. Input is BusinessUnit.id"""
    # Get the BusinessUnit
    #bu_id = int(bu_id)
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    machine_groups = business_unit.machinegroup_set.all()
    count = 0
    for machinegroup in machine_groups:
        count = count + machinegroup.machine_set.count()
    return count

@register.filter
def convert_datetime(string):
    """Converts a string into a date object"""
    the_date = dateutil.parser.parse(string).replace(tzinfo=utc)
#
    #return date(the_date, "Y-m-d H:i")
    return the_date
