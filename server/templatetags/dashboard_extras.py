import time
from distutils.version import LooseVersion

import dateutil.parser

from django import template
from django.shortcuts import get_object_or_404
from django.utils.timezone import utc

import utils.text_utils
from server.models import MachineGroup, BusinessUnit


register = template.Library()


@register.filter
def human_readable_size(size_in_bytes, base2=True):
    """Returns sizes in human-readable units.

    Args:
        size_in_bytes (int, float): Size to convert.
        base2 (bool): Use base2 sizes (kibibytes, etc).

    Returns:
        str rounded to 1 precision and converted to desired sizing
        units.
    """
    size_in_bytes = float(size_in_bytes)
    base, suffix = (1024.0, 'iB') if base2 else (1000.0, 'B')
    # Build an iterable of suffixes to work through.
    for x in ['B'] + list(map(lambda x: x + suffix, list('kMGTP'))):
        if -base < size_in_bytes < base:
            return f"{size_in_bytes:3.1f} {x}"
        size_in_bytes /= base
        return f"{size_in_bytes:3.1f} {x}"


human_readable_size.is_safe = True


@register.filter
def cat(arg1, arg2):
    """Concatenate arg1 & arg2."""
    return "{}{}".format(arg1, arg2)


@register.filter
def macos(os_version):
    if LooseVersion(os_version) > LooseVersion('10.11.99'):
        return 'macOS'
    else:
        return 'OS X'


@register.filter
def bu_machine_count(bu_id):
    """Returns the number of machines contained within the child Machine Groups. Input is
    BusinessUnit.id"""
    # Get the BusinessUnit
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    machine_groups = business_unit.machinegroup_set.all()
    count = 0
    for machinegroup in machine_groups:
        count = count + machinegroup.machine_set.filter(deployed=True).count()
    return count


@register.filter
def machine_group_count(group_id):
    """Returns the number of machines contained within the Machine Group.
    Input is machineGroup.id"""
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    count = machine_group.machine_set.filter(deployed=True).count()
    return count


@register.filter
def convert_datetime(string):
    """Converts a string into a date object"""
    the_date = dateutil.parser.parse(string).replace(tzinfo=utc)
    return the_date


@register.filter
def print_timestamp(timestamp):
    try:
        # assume, that timestamp is given in seconds with decimal point
        ts = float(timestamp)
    except ValueError:
        return None
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


@register.filter
def stringify(data):
    return utils.text_utils.stringify(data)


@register.filter
def sort(data):
    return sorted(data)


@register.filter
def dict_lookup(hash, key):
    return hash[key]


@register.filter
def next(value, arg):
    try:
        return value[int(arg) + 1]
    except Exception:
        return None
