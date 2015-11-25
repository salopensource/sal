# Create your views here.
from models import *
from inventory.models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
import json
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from datetime import datetime, timedelta, date
from django.db.models import Count, Sum, Max, Q
from django.contrib import messages
from django.contrib.staticfiles.templatetags.staticfiles import static
import plistlib
import ast
from forms import *
import pprint
import re
import os
from yapsy.PluginManager import PluginManager
from django.core.exceptions import PermissionDenied
import utils
import pytz
import watson
import unicodecsv as csv
import django.utils.timezone
import dateutil.parser
import hashlib
# This will only work if BRUTE_PROTECT == True
try:
    import axes.utils
except:
    pass

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)

@csrf_exempt
@login_required
def search(request):
    user = request.user
    user_level = user.userprofile.level
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
    else:
        raise Http404
    # Make sure we're searching across Machines the user has access to:
    machines = Machine.objects.all()
    if user_level == 'GA':
        machines = machines
    else:
        for business_unit in BusinessUnit.objects.all():
            if business_unit not in user.businessunit_set.all():
                machines = machines.exclude(machine_group__business_unit = business_unit)
    if query_string.lower().startswith('facter:'):
        query_string = query_string.replace('facter:','').replace('Facter:', '').strip()
        machines = Fact.objects.filter(machine=machines)
        template = 'server/search_facter.html'
    elif query_string.lower().startswith('condition:'):
        query_string = query_string.replace('condition:','').replace('Condition:', '').strip()
        machines = Condition.objects.filter(machine=machines)
        template = 'server/search_condition.html'
    elif query_string.lower().startswith('inventory:'):
        query_string = query_string.replace('inventory:','').replace('Inventory:', '').strip()
        machines = InventoryItem.objects.filter(machine=machines)
        template = 'server/search_inventory.html'
    else:
        template = 'server/search_machines.html'
    search_results = watson.filter(machines, query_string)

    title = "Search results for %s" % query_string
    c = {'user': request.user, 'search_results': search_results, 'title':title, 'request':request}
    return render_to_response(template, c, context_instance=RequestContext(request))

@login_required
def index(request):
    # Get the current user's Business Units
    user = request.user
    # Count the number of users. If there is only one, they need to be made a GA
    if User.objects.count() == 1:
        # The first user created by syncdb won't have a profile. If there isn't one, make sure they get one.
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=user)

        profile.level = 'GA'
        profile.save()
    user_level = user.userprofile.level
    now = django.utils.timezone.now()
    hour_ago = now - timedelta(hours=1)
    today = now - timedelta(hours=24)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    config_installed = 'config' in settings.INSTALLED_APPS
    if user_level != 'GA':
        # user has many BU's display them all in a friendly manner
        business_units = user.businessunit_set.all()
        if user.businessunit_set.count() == 0:
            c = {'user': request.user, }
            return render_to_response('server/no_access.html', c, context_instance=RequestContext(request))
        if user.businessunit_set.count() == 1:
            # user only has one BU, redirect to it
            for bu in user.businessunit_set.all():
                return redirect('server.views.bu_dashboard', bu_id=bu.id)
                break

    # Load in the default plugins if needed
    utils.loadDefaultPlugins()
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            # If plugin_type isn't set, assume its an old style one
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except:
                plugin_type = 'old'
            if plugin.name == enabled_plugin.name and \
            plugin_type != 'machine_info' and plugin_type != 'front_full':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output)
    # get the user level - if they're a global admin, show all of the machines. If not, show only the machines they have access to
    if user_level == 'GA':
        business_units = BusinessUnit.objects.all()
    else:
        business_units = user.businessunit_set.all()

    c = {'user': request.user, 'business_units': business_units, 'output': output, }
    return render_to_response('server/index.html', c, context_instance=RequestContext(request))

# Manage Users
@login_required
def manage_users(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)

    try:
        brute_protect = settings.BRUTE_PROTECT
    except:
        brute_protect = False
    # We require you to be staff to manage users
    if user.is_staff != True:
        return redirect(index)
    users = User.objects.all()
    c = {'user':request.user, 'users':users, 'request':request, 'brute_protect':brute_protect}
    return render_to_response('server/manage_users.html', c, context_instance=RequestContext(request))

# Unlock account
@login_required
def brute_unlock(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)

    try:
        brute_protect = settings.BRUTE_PROTECT
    except:
        brute_protect = False
    if brute_protect == False:
        return redirect(index)
    # We require you to be staff to manage users
    if user.is_staff != True:
        return redirect(index)
    axes.utils.reset()
    c = {'user':request.user, 'request':request, 'brute_protect':brute_protect}
    return render_to_response('server/brute_unlock.html', c, context_instance=RequestContext(request))

# New User
@login_required
def new_user(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    # We require you to be staff to manage users
    if user.is_staff != True:
        return redirect(index)
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.level=request.POST['user_level']
            user_profile.save()
            return redirect('manage_users')
    else:
        form = NewUserForm()
    c = {'form': form}

    return render_to_response('forms/new_user.html', c, context_instance=RequestContext(request))


@login_required
def edit_user(request, user_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    # We require you to be staff to manage users
    if user.is_staff != True:
        return redirect(index)
    the_user = get_object_or_404(User, pk=int(user_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        if the_user.has_usable_password:
            form = EditUserForm(request.POST)
        else:
            form = EditLDAPUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=the_user)
            user_profile.level=request.POST['user_level']
            user_profile.save()
            if user_profile.level != 'GA':
                user.is_staff = False
                user.save()
            return redirect('manage_users')
    else:
        if the_user.has_usable_password:
            form = EditUserForm({'user_level':the_user.userprofile.level, 'user_id':the_user.id})
        else:
            form = EditLDAPUserForm({'user_level':the_user.userprofile.level, 'user_id':the_user.id})

    c = {'form': form, 'the_user':the_user}

    return render_to_response('forms/edit_user.html', c, context_instance=RequestContext(request))

@login_required
def user_add_staff(request, user_id):
    user_level = request.user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.is_staff = True
    user.save()
    return redirect('manage_users')

@login_required
def user_remove_staff(request, user_id):
    user_level = request.user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.is_staff = False
    user.save()
    return redirect('manage_users')

def delete_user(request, user_id):
    user_level = request.user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.delete()
    return redirect('manage_users')
# Plugin machine list
@login_required
def machine_list(request, pluginName, data, page='front', theID=None):
    user = request.user
    title = None
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines_unsorted = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        else:
            machines_unsorted = None
        machines=machines_unsorted

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)
    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            (machines, title) = plugin.plugin_object.filter_machines(machines, data)
    c = {'user':user, 'plugin_name': pluginName, 'machines': machines, 'req_type': page, 'title': title, 'bu_id': theID, 'request':request, 'data':data }

    return render_to_response('server/overview_list_all.html', c, context_instance=RequestContext(request))

# Plugin machine list
@login_required
def plugin_load(request, pluginName, page='front', theID=None):
    user = request.user
    title = None
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines_unsorted = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        else:
            machines_unsorted = None
        machines=machines_unsorted

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)
    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            html = plugin.plugin_object.widget_content(page, machines, theID)
    # c = {'user':user, 'plugin_name': pluginName, 'machines': machines, 'req_type': page, 'title': title, 'bu_id': theID, 'request':request }

    # return render_to_response('server/overview_list_all.html', c, context_instance=RequestContext(request))
    return HttpResponse(html)


@login_required
def export_csv(request, pluginName, data, page='front', theID=None):
    user = request.user
    title = None
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines_unsorted = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        else:
            machines_unsorted = None
        machines=machines_unsorted

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)
    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            (machines, title) = plugin.plugin_object.filter_machines(machines, data)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title

    writer = csv.writer(response)
    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if not field.is_relation and field.name != 'id' and field.name != 'report' and field.name != 'activity' and field.name != 'os_family':
            header_row.append(field.name)
    header_row.append('business_unit')
    header_row.append('machine_group')
    writer.writerow(header_row)
    for machine in machines:
        row = []
        for name, value in machine.get_fields():
            if name != 'id' and name !='machine_group' and name != 'report' and name != 'activity' and name != 'os_family':
                row.append(value.strip())
        row.append(machine.machine_group.business_unit.name)
        row.append(machine.machine_group.name)
        writer.writerow(row)
        #writer.writerow([machine.serial, machine.machine_group.business_unit.name, machine.machine_group.name,
        #machine.hostname, machine.operating_system, machine.memory, machine.memory_kb, machine.munki_version, machine.manifest])

    return response

# New BU
@login_required
def new_business_unit(request):
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = BusinessUnitForm(request.POST)
        if form.is_valid():
            new_business_unit = form.save(commit=False)
            new_business_unit.save()
            form.save_m2m()
            return redirect('bu_dashboard', new_business_unit.id)
    else:
        form = BusinessUnitForm()
    c = {'form': form}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    return render_to_response('forms/new_business_unit.html', c, context_instance=RequestContext(request))

# Edit BU
@login_required
def edit_business_unit(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        if user.is_staff:
            form = EditUserBusinessUnitForm(request.POST, instance=business_unit)
        else:
            form = EditBusinessUnitForm(request.POST, instance=business_unit)
        if form.is_valid():
            new_business_unit = form.save(commit=False)
            new_business_unit.save()
            form.save_m2m()
            return redirect('bu_dashboard', new_business_unit.id)
    else:
        if user.is_staff:
            form = EditUserBusinessUnitForm(instance=business_unit)
        else:
            form = EditBusinessUnitForm(instance=business_unit)
    c = {'form': form, 'business_unit':business_unit}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    return render_to_response('forms/edit_business_unit.html', c, context_instance=RequestContext(request))

@login_required
def delete_business_unit(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    config_installed = 'config' in settings.INSTALLED_APPS

    machine_groups = business_unit.machinegroup_set.all()
    machines = []
    # for machine_group in machine_groups:
    #     machines.append(machine_group.machine_set.all())

    machines = Machine.objects.filter(machine_group__business_unit=business_unit)

    c = {'user': user, 'business_unit':business_unit, 'config_installed':config_installed, 'machine_groups': machine_groups, 'machines':machines}
    return render_to_response('server/business_unit_delete_confirm.html', c, context_instance=RequestContext(request))

@login_required
def really_delete_business_unit(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    business_unit.delete()
    return redirect(index)

# BU Dashboard
@login_required
def bu_dashboard(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    bu = business_unit
    config_installed = 'config' in settings.INSTALLED_APPS
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)
    # Get the groups within the Business Unit
    machine_groups = business_unit.machinegroup_set.all()
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False
    machines = utils.getBUmachines(bu_id)
    now = django.utils.timezone.now()
    hour_ago = now - timedelta(hours=1)
    today = now - timedelta(hours=24)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)

    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            if plugin.name == enabled_plugin.name:
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'bu_dashboard', bu.id)

    c = {'user': request.user, 'machine_groups': machine_groups, 'is_editor': is_editor, 'business_unit': business_unit, 'user_level': user_level, 'output':output, 'config_installed':config_installed }
    return render_to_response('server/bu_dashboard.html', c, context_instance=RequestContext(request))

# Overview list (all)
@login_required
def overview_list_all(request, req_type, data, bu_id=None):
    # get all the BU's that the user has access to
    user = request.user
    user_level = user.userprofile.level
    operating_system = None
    activity = None
    inactivity = None
    disk_space = None
    now = django.utils.timezone.now()
    hour_ago = now - timedelta(hours=1)
    today = now - timedelta(hours=24)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    mem_4_gb = 4 * 1024 * 1024
    mem_415_gb = 4.15 * 1024 * 1024
    mem_775_gb = 7.75 * 1024 * 1024
    mem_8_gb = 8 * 1024 * 1024
    if req_type == 'operating_system':
        operating_system = data

    if req_type == 'activity':
        activity = data

    if req_type == 'inactivity':
        inactivity = data

    if req_type == 'disk_space_ok':
        disk_space_ok = data

    if req_type == 'disk_space_warning':
        disk_space_warning = data

    if req_type == 'disk_space_alert':
        disk_space_alert = data

    if req_type == 'mem_ok':
        disk_space_alert = data

    if req_type == 'mem_warning':
        disk_space_alert = data

    if req_type == 'mem_alert':
        disk_space_alert = data

    if req_type == 'pending_updates':
        pending_update = data

    if req_type == 'pending_apple_updates':
        pending_apple_update = data

    if bu_id != None:
        business_units = get_object_or_404(BusinessUnit, pk=bu_id)
        machine_groups = MachineGroup.objects.filter(business_unit=business_units).prefetch_related('machine_set').all()

        machines_unsorted = machine_groups[0].machine_set.all()
        for machine_group in machine_groups[1:]:
            machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        all_machines=machines_unsorted
        # check user is allowed to see it
        if business_units not in user.businessunit_set.all():
            if user_level != 'GA':
                print 'not letting you in ' + user_level
                return redirect(index)
    else:
        # all BUs the user has access to
        business_units = user.businessunit_set.all()
        # get all the machine groups
        # business_unit = business_units[0].machinegroup_set.all()
        machines_unsorted = Machine.objects.none()
        for business_unit in business_units:
            for machine_group in business_unit.machinegroup_set.all():
                #print machines_unsorted
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()
            #machines_unsorted = machines_unsorted | machine_group.machines.all()
        #machines = user.businessunit_set.select_related('machine_group_set').order_by('machine')
        all_machines = machines_unsorted
        if user_level == 'GA':
            business_units = BusinessUnit.objects.all()
            all_machines = Machine.objects.all()

    if req_type == 'errors':
        machines = all_machines.filter(errors__gt=0)

    if req_type == 'warnings':
        machines = all_machines.filter(warnings__gt=0)

    if req_type == 'active':
        machines = all_machines.filter(activity__isnull=False)

    if req_type == 'disk_space_ok':
        machines = all_machines.filter(hd_percent__lt=80)

    if req_type == 'disk_space_warning':
        machines = all_machines.filter(hd_percent__range=["80", "89"])

    if req_type == 'disk_space_alert':
        machines = all_machines.filter(hd_percent__gte=90)

    if req_type == 'mem_ok':
        machines = all_machines.filter(memory_kb__gte=mem_8_gb)

    if req_type == 'mem_warning':
        machines = all_machines.filter(memory_kb__range=[mem_4_gb, mem_775_gb])

    if req_type == 'mem_alert':
        machines = all_machines.filter(memory_kb__lt=mem_4_gb)

    if req_type == 'uptime_ok':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1)

    if req_type == 'uptime_warning':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7])

    if req_type == 'uptime_alert':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7)

    if activity is not None:
        if data == '1-hour':
            machines = all_machines.filter(last_checkin__gte=hour_ago)
        if data == 'today':
            machines = all_machines.filter(last_checkin__gte=today)
        if data == '1-week':
            machines = all_machines.filter(last_checkin__gte=week_ago)
    if inactivity is not None:
        if data == '1-month':
            machines = all_machines.filter(last_checkin__range=(three_months_ago, month_ago))
        if data == '3-months':
            machines = all_machines.exclude(last_checkin__gte=three_months_ago)

    if operating_system is not None:
        machines = all_machines.filter(operating_system__exact=operating_system)

    if req_type == 'pending_updates':
        machines = all_machines.filter(pendingupdate__update=pending_update)

    if req_type == 'pending_apple_updates':
        machines = all_machines.filter(pendingappleupdate__update=pending_apple_update)
    c = {'user':user, 'machines': machines, 'req_type': req_type, 'data': data, 'bu_id': bu_id }

    return render_to_response('server/overview_list_all.html', c, context_instance=RequestContext(request))

# Machine Group Dashboard
@login_required
def group_dashboard(request, group_id):
    # check user is allowed to access this
    user = request.user
    config_installed = 'config' in settings.INSTALLED_APPS
    user_level = user.userprofile.level
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False
    machines = machine_group.machine_set.all()
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            if plugin.name == enabled_plugin.name:
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'group_dashboard', machine_group.id)
    c = {'user': request.user, 'machine_group': machine_group, 'user_level': user_level,  'is_editor': is_editor, 'business_unit': business_unit, 'output':output, 'config_installed':config_installed, 'request':request}
    return render_to_response('server/group_dashboard.html', c, context_instance=RequestContext(request))

# New Group
@login_required
def new_machine_group(request, bu_id):
    c = {}
    c.update(csrf(request))
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    if request.method == 'POST':
        form = MachineGroupForm(request.POST)
        if form.is_valid():
            new_machine_group = form.save(commit=False)
            new_machine_group.business_unit = business_unit
            new_machine_group.save()
            #form.save_m2m()
            return redirect('group_dashboard', new_machine_group.id)
    else:
        form = MachineGroupForm()

    user = request.user
    user_level = user.userprofile.level
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False

    if business_unit not in user.businessunit_set.all() or is_editor == False:
        if user_level != 'GA':
            return redirect(index)
    c = {'form': form, 'is_editor': is_editor, 'business_unit': business_unit, }
    return render_to_response('forms/new_machine_group.html', c, context_instance=RequestContext(request))

# Edit Group
@login_required
def edit_machine_group(request, group_id):
    c = {}
    c.update(csrf(request))
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    user = request.user
    user_level = user.userprofile.level
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False

    if business_unit not in user.businessunit_set.all() or is_editor == False:
        if user_level != 'GA':
            return redirect(index)
    if request.method == 'POST':
        form = EditMachineGroupForm(request.POST, instance=machine_group)
        if form.is_valid():
            machine_group.save()
            #form.save_m2m()
            return redirect('group_dashboard', machine_group.id)
    else:
        form = EditMachineGroupForm(instance=machine_group)

    c = {'form': form, 'is_editor': is_editor, 'business_unit': business_unit, 'machine_group':machine_group}
    return render_to_response('forms/edit_machine_group.html', c, context_instance=RequestContext(request))

# Delete Group

# New machine
@login_required
def new_machine(request, group_id):
    c = {}
    c.update(csrf(request))
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    if request.method == 'POST':
        form = NewMachineForm(request.POST)
        if form.is_valid():
            new_machine = form.save(commit=False)
            new_machine.machine_group = machine_group
            new_machine.save()
            #form.save_m2m()
            return redirect('machine_detail', new_machine.id)
    else:
        form = NewMachineForm()

    user = request.user
    user_level = user.userprofile.level
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False

    if business_unit not in user.businessunit_set.all() or is_editor == False:
        if user_level != 'GA':
            return redirect(index)
    c = {'form': form, 'is_editor': is_editor, 'machine_group': machine_group, }
    return render_to_response('forms/new_machine.html', c, context_instance=RequestContext(request))

# Machine detail
@login_required
def machine_detail(request, machine_id):
    try:
        machine = Machine.objects.get(pk=machine_id)
    except (ValueError, Machine.DoesNotExist):
        machine = get_object_or_404(Machine, serial=machine_id)
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit
    # check the user is in a BU that's allowed to see this Machine
    user = request.user
    user_level = user.userprofile.level
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)

    report = machine.get_report()
    if machine.facts.count() != 0:
        facts = machine.facts.all()
        if settings.EXCLUDED_FACTS:
            for excluded in settings.EXCLUDED_FACTS:
                facts = facts.exclude(fact_name=excluded)
    else:
        facts = None

    if machine.conditions.count() != 0:
        conditions = machine.conditions.all()
        # get the IP address(es) from the condition
        try:
            ip_address = conditions.get(machine=machine, condition_name__exact='ipv4_address')
            ip_address = ip_address.condition_data
        except:
            ip_address = None
        if settings.EXCLUDED_CONDITIONS:
            for excluded in settings.EXCLUDED_CONDITIONS:
                conditions = conditions.exclude(condition_name=excluded)
    else:
        conditions = None
        ip_address = None

    install_results = {}
    for result in report.get('InstallResults', []):
        nameAndVers = result['name'] + '-' + result['version']
        if result['status'] == 0:
            install_results[nameAndVers] = "installed"
        else:
            install_results[nameAndVers] = 'error'

    if install_results:
        for item in report.get('ItemsToInstall', []):
            name = item.get('display_name', item['name'])
            nameAndVers = ('%s-%s'
                % (name, item['version_to_install']))
            item['install_result'] = install_results.get(
                nameAndVers, 'pending')

        for item in report.get('ManagedInstalls', []):
            if 'version_to_install' in item:
                name = item.get('display_name', item['name'])
                nameAndVers = ('%s-%s'
                    % (name, item['version_to_install']))
                if install_results.get(nameAndVers) == 'installed':
                    item['installed'] = True

    # handle items that were removed during the most recent run
    # this is crappy. We should fix it in Munki.
    removal_results = {}
    for result in report.get('RemovalResults', []):
        m = re.search('^Removal of (.+): (.+)$', result)
        if m:
            try:
                if m.group(2) == 'SUCCESSFUL':
                    removal_results[m.group(1)] = 'removed'
                else:
                    removal_results[m.group(1)] = m.group(2)
            except IndexError:
                pass

    if removal_results:
        for item in report.get('ItemsToRemove', []):
            name = item.get('display_name', item['name'])
            item['install_result'] = removal_results.get(
                name, 'pending')
            if item['install_result'] == 'removed':
                if not 'RemovedItems' in report:
                    report['RemovedItems'] = [item['name']]
                elif not name in report['RemovedItems']:
                    report['RemovedItems'].append(item['name'])

    config_installed = 'config' in settings.INSTALLED_APPS

    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()
        if config_installed:
            from config.views import filter_uninstalls
            report['managed_uninstalls_list'] = filter_uninstalls(business_unit.id, report['managed_uninstalls_list'])


    c = {'user':user, 'machine_group': machine_group, 'business_unit': business_unit, 'report': report, 'install_results': install_results, 'removal_results': removal_results, 'machine': machine, 'facts':facts, 'conditions':conditions, 'ip_address':ip_address, 'config_installed':config_installed }
    return render_to_response('server/machine_detail.html', c, context_instance=RequestContext(request))

# Edit Machine

# Delete Machine
@login_required
def delete_machine(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit
    user = request.user
    user_level = user.userprofile.level
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)
    machine.delete()
    return redirect('group_dashboard', machine_group.id)


@login_required
def settings_page(request):
    user = request.user
    user_level = user.userprofile.level

    # Pull the historical_data setting
    try:
        historical_setting = SalSetting.objects.get(name='historical_retention')
    except SalSetting.DoesNotExist:
        historical_setting = SalSetting(name='historical_retention', value='180')
        historical_setting.save()
    historical_setting_form = SettingsHistoricalDataForm(initial={'days': historical_setting.value})
    if user_level != 'GA':
        return redirect(index)

    c = {'user':request.user, 'request':request, 'historical_setting_form':historical_setting_form}
    return render_to_response('server/settings.html', c, context_instance=RequestContext(request))

@login_required
def settings_historical_data(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SettingsHistoricalDataForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            try:
                historical_setting = SalSetting.objects.get(name='historical_retention')
            except SalSetting.DoesNotExist:
                historical_setting = SalSetting(name='historical_retention')

            historical_setting.value = form.cleaned_data['days']
            historical_setting.save()
            messages.success(request, 'Data retention settings saved.')

            return redirect('settings_page')

    else:
        return redirect('settings_page')
@login_required
def plugins_page(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    # Load the plugins
    utils.reloadPluginsModel()
    enabled_plugins = Plugin.objects.all()
    disabled_plugins = utils.disabled_plugins()
    c = {'user':request.user, 'request':request, 'enabled_plugins':enabled_plugins, 'disabled_plugins':disabled_plugins}
    return render_to_response('server/plugins.html', c, context_instance=RequestContext(request))

@login_required
def plugin_plus(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')

    # get current plugin order
    current_plugin = get_object_or_404(Plugin, pk=plugin_id)

    # get 'old' next one
    old_plugin = get_object_or_404(Plugin, order=(int(current_plugin.order)+1))
    current_plugin.order = current_plugin.order + 1
    current_plugin.save()

    old_plugin.order = old_plugin.order - 1
    old_plugin.save()
    return redirect('plugins_page')

@login_required
def plugin_minus(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')

    # get current plugin order
    current_plugin = get_object_or_404(Plugin, pk=plugin_id)
    #print current_plugin
    # get 'old' previous one

    old_plugin = get_object_or_404(Plugin, order=(int(current_plugin.order)-1))
    current_plugin.order = current_plugin.order - 1
    current_plugin.save()

    old_plugin.order = old_plugin.order + 1
    old_plugin.save()
    return redirect('plugins_page')

@login_required
def plugin_disable(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')
    plugin = get_object_or_404(Plugin, pk=plugin_id)
    plugin.delete()
    return redirect('plugins_page')

@login_required
def plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = Plugin(name=plugin_name, order=utils.UniquePluginOrder())
        plugin.save()
    return redirect('plugins_page')

@login_required
def api_keys(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)

    api_keys = ApiKey.objects.all()
    c = {'user':request.user, 'api_keys':api_keys, 'request':request}
    return render_to_response('server/api_keys.html', c, context_instance=RequestContext(request))

@login_required
def new_api_key(request):
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            new_api_key = form.save()
            return redirect('display_api_key', key_id=new_api_key.id)
    else:
        form = ApiKeyForm()
    c = {'form': form}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    return render_to_response('forms/new_api_key.html', c, context_instance=RequestContext(request))

@login_required
def display_api_key(request, key_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    if api_key.has_been_seen == True:
        return redirect(index)
    else:
        api_key.has_been_seen = True
        api_key.save()
        c = {'user':request.user, 'api_key':api_key, 'request':request}
        return render_to_response('server/api_key_display.html', c, context_instance=RequestContext(request))

@login_required
def edit_api_key(request, key_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':

        form = ApiKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            api_key = form.save()
            return redirect(api_keys)
    else:
        form = ApiKeyForm(instance=api_key)
    c = {'form': form, 'api_key':api_key}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    return render_to_response('forms/edit_api_key.html', c, context_instance=RequestContext(request))

@login_required
def delete_api_key(request, key_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    api_key.delete()
    return redirect(api_keys)

# preflight
@csrf_exempt
def preflight(request):
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = {}
    output['queries'] = {}
    for plugin in manager.getAllPlugins():
        counter = 0
        try:
            if plugin.plugin_object.plugin_type() == 'osquery':
                # No other plugins will have info for this
                for query in plugin.plugin_object.get_queries():
                    name = query['name']
                    del query['name']
                    output['queries'][name] = {}
                    output['queries'][name] = query

        except:
            pass
    return HttpResponse(json.dumps(output))


# checkin
@csrf_exempt
def checkin(request):
    if request.method != 'POST':
        print 'not post data'
        raise Http404

    data = request.POST
    key = data.get('key')
    serial = data.get('serial')
    serial = serial.upper()

    # Take out some of the weird junk VMware puts in. Keep an eye out in case Apple actually uses these:
    serial = serial.replace('/', '')
    serial = serial.replace('+', '')

    # Are we using Sal for some sort of inventory (like, I don't know, Puppet?)
    try:
        add_new_machines = settings.ADD_NEW_MACHINES
    except:
        add_new_machines = True

    if add_new_machines == True:
        # look for serial number - if it doesn't exist, create one
        if serial:
            try:
                machine = Machine.objects.get(serial=serial)
            except Machine.DoesNotExist:
                machine = Machine(serial=serial)
    else:
        machine = get_object_or_404(Machine, serial=serial)

    if key is None or key == 'None':
        try:
            key = settings.DEFAULT_MACHINE_GROUP_KEY
        except Exception:
            pass

    machine_group = get_object_or_404(MachineGroup, key=key)

    business_unit = machine_group.business_unit
    try:
        historical_setting = SalSetting.objects.get(name='historical_retention')
        historical_days = historical_setting.value
    except SalSetting.DoesNotExist:
        historical_setting = SalSetting(name='historical_retention', value='180')
        historical_setting.save()
        historical_days = '180'

    if machine:
        machine.hostname = data.get('name', '<NO NAME>')
        try:
            use_enc = settings.USE_ENC
            # If we're using Sal's Puppet ENC, don't change the machine group,
            # as we're setting it in the GUI
        except:
            use_enc = False

        if use_enc == False:
            machine.machine_group = machine_group
        machine.last_checkin = datetime.now()
        if 'username' in data:
            machine.username = data.get('username')
        if 'base64bz2report' in data:
            machine.update_report(data.get('base64bz2report'))

        if 'sal_version' in data:
            machine.sal_version = data.get('sal_version')

        # extract machine data from the report
        report_data = machine.get_report()
        if 'Puppet_Version' in report_data:
            machine.puppet_version = report_data['Puppet_Version']
        if 'ManifestName' in report_data:
            manifest = report_data['ManifestName']
            machine.manifest = manifest
        if 'MachineInfo' in report_data:
            machine.operating_system = report_data['MachineInfo'].get(
                'os_vers', 'UNKNOWN')
            # some machines are reporting 10.9, some 10.9.0 - make them the same
            if len(machine.operating_system) <= 4:
                machine.operating_system = machine.operating_system + '.0'
        machine.hd_space = report_data.get('AvailableDiskSpace') or 0
        machine.hd_total = int(data.get('disk_size')) or 0

        machine.hd_percent = int(round(((float(machine.hd_total)-float(machine.hd_space))/float(machine.hd_total))*100))
        machine.munki_version = report_data.get('ManagedInstallVersion') or 0
        hwinfo = {}
        if 'SystemProfile' in report_data.get('MachineInfo', []):
            for profile in report_data['MachineInfo']['SystemProfile']:
                if profile['_dataType'] == 'SPHardwareDataType':
                    hwinfo = profile._items[0]
                    break

        if 'Puppet' in report_data:
            puppet = report_data.get('Puppet')
            if 'time' in puppet:
                machine.last_puppet_run = datetime.fromtimestamp(float(puppet['time']['last_run']))
            if 'events' in puppet:
                machine.puppet_errors = puppet['events']['failure']

        if hwinfo:
            machine.machine_model = hwinfo.get('machine_model')
            machine.cpu_type = hwinfo.get('cpu_type')
            machine.cpu_speed = hwinfo.get('current_processor_speed')
            machine.memory = hwinfo.get('physical_memory')

            if hwinfo.get('physical_memory')[-2:] == 'MB':
                memory_mb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_mb * 1024)
            if hwinfo.get('physical_memory')[-2:] == 'GB':
                memory_gb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_gb * 1024 * 1024)
            if hwinfo.get('physical_memory')[-2:] == 'TB':
                memory_tb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_tb * 1024 * 1024 * 1024)

        if 'os_family' in report_data:
            machine.os_family = report_data['os_family']

        machine.save()


        # Remove existing PendingUpdates for the machine
        updates = machine.pending_updates.all()
        updates.delete()
        now = datetime.now()
        if 'ItemsToInstall' in report_data:
            for update in report_data.get('ItemsToInstall'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()
                # Let's handle some of those lovely pending installs into the UpdateHistory Model
                try:
                    update_history = UpdateHistory.objects.get(name=update_name, version=version, machine=machine, update_type='third_party')
                except UpdateHistory.DoesNotExist:
                    update_history = UpdateHistory(name=update_name, version=version, machine=machine, update_type='third_party')
                    update_history.save()

                if update_history.pending_recorded == False:
                    update_history_item = UpdateHistoryItem(update_history=update_history, status='pending', recorded=now)
                    update_history_item.save()
                    update_history.pending_recorded = True
                    update_history.save()


        # Remove existing PendingAppleUpdates for the machine
        updates = machine.pending_apple_updates.all()
        updates.delete()
        if 'AppleUpdates' in report_data:
            for update in report_data.get('AppleUpdates'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingAppleUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()
                # Let's handle some of those lovely pending installs into the UpdateHistory Model
                try:
                    update_history = UpdateHistory.objects.get(name=update_name, version=version, machine=machine, update_type='apple')
                except UpdateHistory.DoesNotExist:
                    update_history = UpdateHistory(name=update_name, version=version, machine=machine, update_type='apple')
                    update_history.save()

                if update_history.pending_recorded == False:
                    update_history_item = UpdateHistoryItem(update_history=update_history, status='pending', recorded=now)
                    update_history_item.save()
                    update_history.pending_recorded = True
                    update_history.save()



        # if Facter data is submitted, we need to first remove any existing facts for this machine
        if 'Facter' in report_data:
            facts = machine.facts.all()
            facts.delete()
            # Delete old historical facts

            try:
                datelimit = datetime.now() - timedelta(days=historical_days)
                HistoricalFact.objects.filter(fact_recorded__lt=datelimit).delete()
            except Exception:
                pass
            try:
                historical_facts = settings.HISTORICAL_FACTS
            except Exception:
                historical_facts = []
                pass
            # now we need to loop over the submitted facts and save them
            for fact_name, fact_data in report_data['Facter'].iteritems():
                fact = Fact(machine=machine, fact_name=fact_name, fact_data=fact_data)
                fact.save()
                if fact_name in historical_facts:
                    fact = HistoricalFact(machine=machine, fact_name=fact_name, fact_data=fact_data, fact_recorded=datetime.now())
                    fact.save()

        if 'Conditions' in report_data:
            conditions = machine.conditions.all()
            conditions.delete()
            for condition_name, condition_data in report_data['Conditions'].iteritems():
                # if it's a list (more than one result), we're going to conacetnate it into one comma separated string
                if type(condition_data) == list:
                    result = None
                    for item in condition_data:
                        # is this the first loop? If so, no need for a comma
                        if result:
                            result = result + ', '+str(item)
                        else:
                            result = item
                    condition_data = result

                #print condition_data
                condition = Condition(machine=machine, condition_name=condition_name, condition_data=str(condition_data))
                condition.save()

        if 'osquery' in report_data:
            try:
                datelimit = (datetime.now() - timedelta(days=historical_days)).strftime("%s")
                OSQueryResult.objects.filter(unix_time__lt=datelimit).delete()
            except:
                pass
            for report in report_data['osquery']:
                unix_time = int(report['unixTime'])
                # Have we already processed this report?
                try:
                    osqueryresult = OSQueryResult.objects.get(hostidentifier=report['hostIdentifier'], machine=machine, unix_time=unix_time, name=report['name'])
                    continue
                except OSQueryResult.DoesNotExist:
                    osqueryresult = OSQueryResult(hostidentifier=report['hostIdentifier'], machine=machine, unix_time=unix_time, name=report['name'])
                    osqueryresult.save()

                for items in report['diffResults']['added']:
                    for column, col_data in items.items():
                        osquerycolumn = OSQueryColumn(osquery_result=osqueryresult, action='added', column_name=column, column_data=col_data)
                        osquerycolumn.save()

                for item in report['diffResults']['removed']:
                    for column, col_data in items.items():
                        osquerycolumn = OSQueryColumn(osquery_result=osqueryresult, action='removed', column_name=column, column_data=col_data)
                        osquerycolumn.save()

        return HttpResponse("Sal report submmitted for %s"
                            % data.get('name'))

@csrf_exempt
def install_log_hash(request, serial):
    sha256hash = ''
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
            sha256hash = machine.install_log_hash
        except (Machine.DoesNotExist, Inventory.DoesNotExist):
            pass
    else:
        return HttpResponse("MACHINE NOT FOUND")
    return HttpResponse(sha256hash)

def process_update_item(name, version, update_type, action, recorded, machine, extra=None):
    # Get a parent update history item, or create one
    try:
        update_history = UpdateHistory.objects.get(name=name,
        version=version,
        update_type=update_type,
        machine=machine)
    except UpdateHistory.DoesNotExist:
        update_history = UpdateHistory(name=name,
        version=version,
        update_type=update_type,
        machine=machine)
        update_history.save()

    # Now make sure it's not already in there
    try:
        update_history_item = UpdateHistoryItem.objects.get(
        recorded=recorded,
        status=action,
        update_history=update_history)
    except UpdateHistoryItem.DoesNotExist:
        # Make one if it doesn't exist
        update_history_item = UpdateHistoryItem(
        recorded=recorded,
        status=action,
        update_history=update_history)
        update_history_item.save()
        if extra:
            update_history_item.extra = extra
            update_history_item.save()

        if action == 'install' or action == 'removal':
            update_history.pending_recorded = False
            update_history.save()

@csrf_exempt
def install_log_submit(request):
    if request.method != 'POST':
        raise Http404


    submission = request.POST
    serial = submission.get('serial')
    key = submission.get('key')
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            raise Http404

        # Check the key
        machine_group = get_object_or_404(MachineGroup, key=key)
        if machine_group.id != machine.machine_group.id:
            raise Http404

        compressed_log= submission.get('base64bz2installlog')
        if compressed_log:
            compressed_log = compressed_log.replace(" ", "+")
            log_str = utils.decode_to_string(compressed_log)
            machine.install_log = log_str
            machine.save()

            for line in log_str.splitlines():
                # Third party install successes first
                m = re.search('(.+) Install of (.+): (.+)$', line)
                if m:
                    try:
                        if m.group(3) == 'SUCCESSFUL':
                            the_date = dateutil.parser.parse(m.group(1))
                            (name, version) = m.group(2).rsplit('-',1)
                            process_update_item(name, version, 'third_party', 'install', the_date,
                            machine)
                            # We've processed this line, move on
                            continue

                    except IndexError:
                        pass
                # Third party install failures
                m = re.search('(.+) Install of (.+): FAILED (.+)$', line)
                if m:
                    try:
                        the_date = dateutil.parser.parse(m.group(1))
                        (name, version) = m.group(2).rsplit('-',1)
                        extra = m.group(3)
                        process_update_item(name, version, 'third_party', 'error', the_date,
                        machine, extra)
                        # We've processed this line, move on
                        continue

                    except IndexError:
                        pass

                # Third party removals
                m = re.search('(.+) Removal of (.+): (.+)$', line)
                if m:
                    try:
                        if m.group(3) == 'SUCCESSFUL':
                            the_date = dateutil.parser.parse(m.group(1))
                            (name, version) = m.group(2).rsplit('-',1)
                            process_update_item(name, version, 'third_party', 'removal', the_date,
                            machine)
                            # We've processed this line, move on
                            continue

                    except IndexError:
                        pass
                # Third party removal failures
                m = re.search('(.+) Removal of (.+): FAILED (.+)$', line)
                if m:
                    try:
                        the_date = dateutil.parser.parse(m.group(1))
                        (name, version) = m.group(2).rsplit('-',1)
                        extra = m.group(3)
                        process_update_item(name, version, 'third_party', 'error', the_date,
                        machine, extra)
                        # We've processed this line, move on
                        continue

                    except IndexError:
                        pass

                # Apple update install successes
                m = re.search('(.+) Apple Software Update install of (.+): (.+)$', line)
                if m:
                    try:
                        if m.group(3) == 'FAILED':
                            the_date = dateutil.parser.parse(m.group(1))
                            (name, version) = m.group(2).rsplit('-',1)
                            process_update_item(name, version, 'apple', 'install', the_date,
                            machine)
                            # We've processed this line, move on
                            continue

                    except IndexError:
                        pass

                # Apple install failures
                m = re.search('(.+) Apple Software Update install of (.+): FAILED (.+)$', line)
                if m:
                    try:
                        the_date = dateutil.parser.parse(m.group(1))
                        (name, version) = m.group(2).rsplit('-',1)
                        extra = m.group(3)
                        process_update_item(name, version, 'apple', 'error', the_date,
                        machine, extra)
                        # We've processed this line, move on
                        continue

                    except IndexError:
                        pass
            machine.install_log_hash = \
                hashlib.sha256(log_str).hexdigest()
            machine.install_log = log_str
            machine.save()
        return HttpResponse("Install Log processed for %s" % serial)
