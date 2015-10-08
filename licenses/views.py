from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.context_processors import csrf
from forms import *

import plistlib
import json
from server.models import *
from models import License

@login_required
def index(request):
    '''Sal index page for licenses.'''
    all_licenses = License.objects.all()
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(server.views.index)

    c = {'request':request,
        'licenses': all_licenses,
         'user': request.user,
         'page': 'licenses'}
    return render_to_response('licenses/index.html', c, context_instance=RequestContext(request))

@login_required
def new_license(request):
    '''Creates a new License object'''
    c = {}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(server.views.index)
    c.update(csrf(request))
    if request.method == 'POST':
        form = LicenseForm(request.POST)
        if form.is_valid():
            new_license = form.save()
            return redirect(index)
    else:
        form = LicenseForm()
    c = {'form': form}
    
    return render_to_response('forms/new_license.html', c, context_instance=RequestContext(request))

@login_required
def edit_license(request, license_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(server.views.index)
    license = get_object_or_404(License, pk=license_id)
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':

        form = LicenseForm(request.POST, instance=api_key)
        if form.is_valid():
            license = form.save()
            return redirect(index)
    else:
        form = LicenseForm(instance=license)
    c = {'form': form, 'license':license}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(server.views.index)
    return render_to_response('forms/edit_license.html', c, context_instance=RequestContext(request))

@login_required
def delete_license(request, license_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    license = get_object_or_404(License, pk=license_id)
    license.delete()
    return redirect(index)

def available(request, key, item_name=''):
    '''Returns license seat availability for item_name in plist format.
    Key is item_name, value is boolean.
    For use by Munki client to determine if a given item should be made
    available for optional install.'''
    output_style = request.GET.get('output_style', 'plist')
    if key.endswith('/'):
        key = key[:-1]
    machine_group = get_object_or_404(MachineGroup,key=key)
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
        licenses = License.objects.all().filter(business_unit=business_unit)
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
    machine_group = get_object_or_404(MachineGroup,key=key)
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