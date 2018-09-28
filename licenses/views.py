import json
import plistlib

from django.contrib.auth.decorators import login_required, permission_required
from django.http import (Http404, HttpRequest, HttpResponse, HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, RequestContext, Template
from django.template.context_processors import csrf

from licenses.forms import *
from licenses.models import *
from sal.decorators import *
from server.models import *


@login_required
@required_level(ProfileLevel.global_admin)
def license_index(request):
    """Sal index page for licenses."""
    context = {'request': request,
               'licenses': License.objects.all(),
               'user': request.user,
               'page': 'licenses'}
    return render(request, 'licenses/index.html', context)


@login_required
@required_level(ProfileLevel.global_admin)
def new_license(request):
    """Creates a new License object"""
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(license_index)
    else:
        form = LicenseForm()

    context = {'form': form}

    return render(request, 'forms/new_license.html', context)


@login_required
@required_level(ProfileLevel.global_admin)
def edit_license(request, license_id):
    license = get_object_or_404(License, pk=license_id)

    if request.method == 'POST':
        form = LicenseForm(request.POST, instance=license)
        if form.is_valid():
            license = form.save()
            return redirect(license_index)
    else:
        form = LicenseForm(instance=license)

    context = {'form': form, 'license': license}

    return render(request, 'forms/edit_license.html', context)


@login_required
@required_level(ProfileLevel.global_admin)
def delete_license(request, license_id):
    license = get_object_or_404(License, pk=license_id)
    license.delete()
    return redirect(license_index)


def available(request, key, item_name=''):
    '''Returns license seat availability for item_name in plist format.
    Key is item_name, value is boolean.
    For use by Munki client to determine if a given item should be made
    available for optional install.'''
    output_style = request.GET.get('output_style', 'plist')
    if key.endswith('/'):
        key = key[:-1]
    machine_group = get_object_or_404(MachineGroup, key=key)
    business_unit = machine_group.business_unit
    item_names = []
    if item_name:
        item_names.append(item_name)
    additional_names = request.GET.getlist('name')
    item_names.extend(additional_names)
    info = {}
    if item_names:
        for name in item_names:
            try:
                license = License.objects.get(item_name=name, business_unit=business_unit)
                info[name] = (license.available() > 0)
            except (License.DoesNotExist):
                pass
    else:
        # return everything
        licenses = License.objects.filter(business_unit=business_unit)
        for license in licenses:
            info[license.item_name] = license.available()

    if output_style == 'json':
        return HttpResponse(json.dumps(info), content_type='application/json')
    else:
        return HttpResponse(plistlib.writePlistToString(info),
                            content_type='application/xml')


def usage(request, key, item_name=''):
    '''Returns license info for item_name in plist or json format.'''
    output_style = request.GET.get('output_style', 'plist')
    item_names = []
    if item_name:
        item_names.append(item_name)
    additional_names = request.GET.getlist('name')
    item_names.extend(additional_names)
    info = {}
    machine_group = get_object_or_404(MachineGroup, key=key)
    business_unit = machine_group.business_unit
    for name in item_names:
        try:
            license = License.objects.get(item_name=name, business_unit=business_unit)
            info[name] = {'total': license.total,
                          'used': license.used()}
            # calculate available instead of hitting the db a second time
            info[name]['available'] = (
                info[name]['total'] - info[name]['used'])
        except (License.DoesNotExist):
            info[name] = {}
    if output_style == 'json':
        return HttpResponse(json.dumps(info), content_type='application/json')
    else:
        return HttpResponse(plistlib.writePlistToString(info),
                            content_type='application/xml')
