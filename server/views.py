# Create your views here.
from models import *
from inventory.models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
import json
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404, HttpResponseNotFound, HttpResponseRedirect, JsonResponse, StreamingHttpResponse
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.template.context_processors import csrf
from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime, timedelta, date
from django.db.models import Count, Sum, Max, Q
from django.contrib import messages
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
import plistlib
import ast
from forms import *
import pprint
import re
import os
from distutils.version import LooseVersion
from yapsy.PluginManager import PluginManager
from django.core.exceptions import PermissionDenied
import utils
import pytz
# from watson import search as watson
import unicodecsv as csv
import django.utils.timezone
import dateutil.parser
import hashlib
import time
from sal.decorators import *

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = utils.is_postgres()

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

    if user_level != 'GA':
        # user has many BU's display them all in a friendly manner
        business_units = user.businessunit_set.all()
        if user.businessunit_set.count() == 0:
            c = {'user': request.user, }
            return render(request, 'server/no_access.html', c)
        if user.businessunit_set.count() == 1:
            # user only has one BU, redirect to it
            for bu in user.businessunit_set.all():
                return redirect('bu_dashboard', bu_id=bu.id)
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
    reports = []
    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in manager.getAllPlugins():
            if enabled_report.name == plugin.name:
                # If plugin_type isn't set, it can't be a report
                try:
                    plugin_type = plugin.plugin_object.plugin_type()
                except:
                    plugin_type = 'widget'
                if plugin_type == 'report':
                    data = {}
                    data['name'] = plugin.name
                    data['title'] = plugin.plugin_object.get_title()
                    reports.append(data)

                    break
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            # If plugin_type isn't set, assume its an old style one
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
            plugin_type != 'machine_info' and plugin_type != 'report':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output)
    # get the user level - if they're a global admin, show all of the machines. If not, show only the machines they have access to
    data_setting_decided = True
    if user_level == 'GA':
        business_units = BusinessUnit.objects.all()
        try:
            senddata_setting = SalSetting.objects.get(name='send_data')
        except SalSetting.DoesNotExist:
            data_setting_decided = False
    else:
        business_units = user.businessunit_set.all()

    # This isn't ready. These can just be false / none for now
    # (new_version_available, new_version, current_version) = check_version()
    new_version_available = False
    new_version = False
    current_version = False
    c = {'user': request.user, 'business_units': business_units, 'output': output, 'data_setting_decided':data_setting_decided, 'new_version_available':new_version_available, 'new_version':new_version, 'reports':reports, 'current_version': current_version}
    return render(request, 'server/index.html', c)

def check_version():
    # Get current version
    new_version_available = False
    new_version = None
    current_dir = os.path.dirname(os.path.realpath(__file__))
    version = plistlib.readPlist(os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist'))
    current_version = version['version']
    try:
        # Get version from the server
        current_version_lookup = SalSetting.objects.get(name='current_version')
        server_version = current_version_lookup.value
    except SalSetting.DoesNotExist:
        server_version = None

    # if we've looked for the server version, check to see what we're running
    if server_version:
        should_notify = False
        if LooseVersion(server_version) > LooseVersion(current_version):
            # Have we notified about this version before?
            try:
                last_version_notified_lookup = SalSetting.objects.get(name='last_notified_version')
                last_notified_version = last_version_notified_lookup.value
            except SalSetting.DoesNotExist:
                last_version_notified_lookup = SalSetting(name='last_notified_version', value=server_version)
                last_version_notified_date_lookup = SalSetting(name='last_version_notified_date',
                value=int(time.time()))
                last_notified_version = None
            # if last version notified version is equal to the server version
            if last_notified_version == server_version:
                try:
                    next_notify_date_lookup = SalSetting.objects.get(name='next_notify_date')
                    next_notify_date = next_notify_date_lookup.value
                except:
                    # They've not chosen yet, show it
                    should_notify = True
                    next_notify_date = None
            else:
                should_notify = True
                next_notify_date = None
            # Try and get the last notified date - if it's never, no new version avaialble
            if next_notify_date:
                if next_notify_date != 'never':
                    current_time = time.time()
                    if current_time > next_notify_date:
                        should_notify = True

            if should_notify:
                new_version_available = True
                new_version = server_version
        else:
            try:
                next_notify_date_lookup = SalSetting.objects.get(name='next_notify_date')
                next_notify_date_lookup.delete()
            except SalSetting.DoesNotExist:
                pass

    return new_version_available, new_version, current_version

@login_required
def new_version_never(request):
    if request.user.userprofile.level != 'GA':
        return redirect(index)
    # Don't notify about a new version until there is a new one
    current_version_lookup = SalSetting.objects.get(name='current_version')
    server_version = current_version_lookup.value
    try:
        last_version_notified= SalSetting.objects.get(name='last_notified_version')
    except SalSetting.DoesNotExist:
        last_version_notified = SalSetting(name='last_notified_version')
    last_version_notified.value = server_version
    last_version_notified.save()

    try:
        next_notify_date = SalSetting.objects.get(name='next_notify_date')
    except SalSetting.DoesNotExist:
        next_notify_date = SalSetting(name='next_notify_date')

    next_notify_date.value = 'never'
    next_notify_date.save()
    return redirect(index)

@login_required
def new_version_week(request):
    # Notify again in a week
    pass

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
    return render(request, 'server/manage_users.html', c)


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

    return render(request, 'forms/new_user.html', c)


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

    return render(request, 'forms/edit_user.html', c)

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

def plugin_machines(request, pluginName, data, page='front', theID=None, get_machines=True):
    user = request.user
    title = None
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    if pluginName == 'Status' and data == 'undeployed_machines':
        deployed = False
    else:
        deployed = True
    # get a list of machines (either from the BU or the group)
    if get_machines:
        if page == 'front':
            # get all machines
            if user.userprofile.level == 'GA':
                machines = Machine.objects.all().filter(deployed=deployed)
            else:
                machines = Machine.objects.none()
                for business_unit in user.businessunit_set.all():
                    for group in business_unit.machinegroup_set.all():
                        machines = machines | group.machine_set.all().filter(deployed=deployed)
        if page == 'bu_dashboard':
            # only get machines for that BU
            # Need to make sure the user is allowed to see this
            business_unit = get_object_or_404(BusinessUnit, pk=theID)
            machine_groups = MachineGroup.objects.filter(business_unit=business_unit).all()

            if machine_groups.count() != 0:
                machines_unsorted = machine_groups[0].machine_set.all().filter(deployed=deployed)
                for machine_group in machine_groups[1:]:
                    machines_unsorted = machines_unsorted | machine_group.machine_set.all().filter(deployed=deployed)
            else:
                machines_unsorted = None
            machines=machines_unsorted

        if page == 'group_dashboard':
            # only get machines from that group
            machine_group = get_object_or_404(MachineGroup, pk=theID)
            # check that the user has access to this
            machines = Machine.objects.filter(machine_group=machine_group).filter(deployed=deployed)
    else:
        machines = Machine.objects.none()
    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            (machines, title) = plugin.plugin_object.filter_machines(machines, data)

    return machines, title

# Table ajax for dataTables
@login_required
def tableajax(request, pluginName, data, page='front', theID=None):
    # Pull our variables out of the GET request
    get_data = request.GET['args']
    get_data = json.loads(get_data.decode('string_escape'))
    draw = get_data.get('draw', 0)
    start = int(get_data.get('start', 0))
    length = int(get_data.get('length', 0))
    search_value = ''
    if 'search' in get_data:
        if 'value' in get_data['search']:
            search_value = get_data['search']['value']

    # default ordering
    order_column = 2
    order_direction = 'desc'
    order_name = ''
    if 'order' in get_data:
        order_column = get_data['order'][0]['column']
        order_direction = get_data['order'][0]['dir']
    for column in get_data.get('columns', None):
        if column['data'] == order_column:
            order_name = column['name']
            break

    if pluginName == 'Status' and data == 'undeployed_machines':
        deployed = False
    else:
        deployed = True
    (machines, title) = plugin_machines(request, pluginName, data, page, theID)
    # machines = machines.filter(deployed=deployed)
    if len(order_name) != 0:
        if order_direction == 'desc':
            order_string = "-%s" % order_name
        else:
            order_string = "%s" % order_name

    if len(search_value) != 0:
        searched_machines = machines.filter(Q(hostname__icontains=search_value) | Q(console_user__icontains=search_value) | Q(last_checkin__icontains=search_value)).order_by(order_string)
    else:
        searched_machines = machines.order_by(order_string)

    limited_machines = searched_machines[start:(start+length)]

    return_data = {}
    return_data['draw'] = int(draw)
    return_data['recordsTotal'] = machines.count()
    return_data['recordsFiltered'] = machines.count()

    return_data['data'] = []
    settings_time_zone = None
    try:
        settings_time_zone = pytz.timezone(settings.TIME_ZONE)
    except:
        pass
    for machine in limited_machines:
        if machine.last_checkin:
            #formatted_date = pytz.utc.localize(machine.last_checkin)
            if settings_time_zone:
                formatted_date = machine.last_checkin.astimezone(settings_time_zone).strftime("%Y-%m-%d %H:%M %Z")
            else:
                formatted_date = machine.last_checkin.strftime("%Y-%m-%d %H:%M")
        else:
            formatted_date = ""
        hostname_link = "<a href=\"%s\">%s</a>" % (reverse('machine_detail', args=[machine.id]), machine.hostname)

        list_data = [hostname_link, machine.console_user, formatted_date]
        return_data['data'].append(list_data)

    return JsonResponse(return_data)

# Plugin machine list
@login_required
def machine_list(request, pluginName, data, page='front', theID=None):
    (machines, title) = plugin_machines(request, pluginName, data, page, theID, get_machines=False)
    user = request.user
    c = {'user':user, 'plugin_name': pluginName, 'machines': machines, 'req_type': page, 'title': title, 'bu_id': theID, 'request':request, 'data':data }

    return render(request, 'server/overview_list_all.html', c)

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
            machines = Machine.deployed_objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all().filter(deployed=True)
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).all()

        machines = Machine.deployed_objects.filter(machine_group__in=machine_groups)

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.deployed_objects.filter(machine_group=machine_group)

    if page =='machine_detail':
        machines = Machine.objects.get(pk=theID)

    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            html = plugin.plugin_object.widget_content(page, machines, theID)

    return HttpResponse(html)

@login_required
def report_load(request, pluginName, page='front', theID=None):
    user = request.user
    title = None
    business_unit = None
    machine_group = None
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
            machines = Machine.deployed_objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all().filter(deployed=True)
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).all()

        machines = Machine.deployed_objects.filter(machine_group=machine_groups)

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.deployed_objects.filter(machine_group=machine_group)

    if page =='machine_detail':
        machines = Machine.objects.get(pk=theID)

    output = ''
    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            output = plugin.plugin_object.widget_content(page, machines, theID)

    reports = []
    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in manager.getAllPlugins():
            if enabled_report.name == plugin.name:
                # If plugin_type isn't set, it can't be a report
                try:
                    plugin_type = plugin.plugin_object.plugin_type()
                except:
                    plugin_type = 'widget'
                if plugin_type == 'report':
                    data = {}
                    data['name'] = plugin.name
                    data['title'] = plugin.plugin_object.get_title()
                    reports.append(data)

                    break

    c = {'user': request.user, 'output': output, 'page':page, 'business_unit': business_unit, 'machine_group': machine_group, 'reports': reports}
    return render(request, 'server/display_report.html', c)

class Echo(object):
    """An object that implements just the write method of the file-like interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers):
    row = []
    for name, value in machine.get_fields():
        if name != 'id' and name !='machine_group' and name != 'report' and name != 'activity' and name != 'os_family' and name != 'install_log' and name != 'install_log_hash':
            try:
                row.append(utils.safe_unicode(value))
            except:
                row.append('')

    row.append(machine.machine_group.business_unit.name)
    row.append(machine.machine_group.name)
    return row

def stream_csv(header_row, machines, facter_headers, condition_headers, plugin_script_headers): # Helper function to inject headers
    if header_row:
        yield header_row
    for machine in machines:
        yield get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers)

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
    if pluginName == 'Status' and data == 'undeployed_machines':
        deployed = False
    else:
        deployed = True
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            # machines = Machine.objects.all().prefetch_related('facts','conditions','pluginscriptsubmission_set','pluginscriptsubmission_set__pluginscriptrow_set')
            machines = Machine.objects.all().filter(deployed=deployed).defer('report','activity','os_family','install_log', 'install_log_hash')
        else:
            machines = Machine.objects.none().defer('report','activity','os_family','install_log', 'install_log_hash')
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all().filter(deployed=deployed)
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines = machines | machine_group.machine_set.all().filter(deployed=deployed).defer('report','activity','os_family','install_log', 'install_log_hash')
        else:
            machines = None

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        # machines = Machine.objects.filter(machine_group=machine_group).prefetch_related('facts','conditions','pluginscriptsubmission_set','pluginscriptsubmission_set__pluginscriptrow_set')
        machines = Machine.objects.filter(machine_group=machine_group).filter(deployed=deployed).defer('report','activity','os_family','install_log', 'install_log_hash')

    if page =='machine_detail':
        machines = Machine.objects.get(pk=theID)

    # send the machines and the data to the plugin
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            (machines, title) = plugin.plugin_object.filter_machines(machines, data)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if not field.is_relation and field.name != 'id' and field.name != 'report' and field.name != 'activity' and field.name != 'os_family' and field.name != 'install_log' and field.name != 'install_log_hash':
            header_row.append(field.name)
    # distinct_facts = Fact.objects.values('fact_name').distinct().order_by('fact_name')

    facter_headers = []

    condition_headers = []

    plugin_script_headers = []

    header_row.append('business_unit')
    header_row.append('machine_group')

    response = StreamingHttpResponse(
            (writer.writerow(row) for row in stream_csv(
                                            header_row=header_row,
                                            machines=machines,
                                            facter_headers=facter_headers,
                                            condition_headers=condition_headers,
                                            plugin_script_headers=plugin_script_headers)),
            content_type="text/csv")
    # Create the HttpResponse object with the appropriate CSV header.
    if getattr(settings, 'DEBUG_CSV', False):
        pass
    else:
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title

    #
    #
    # if getattr(settings, 'DEBUG_CSV', False):
    #     writer.writerow(['</body>'])
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
    return render(request, 'forms/new_business_unit.html', c)

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
    return render(request, 'forms/edit_business_unit.html', c)

@login_required
def delete_business_unit(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))

    machine_groups = business_unit.machinegroup_set.all()
    machines = []

    machines = Machine.deployed_objects.filter(machine_group__business_unit=business_unit)

    c = {'user': user, 'business_unit':business_unit, 'machine_groups': machine_groups, 'machines':machines}
    return render(request, 'server/business_unit_delete_confirm.html', c)

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
    reports = []
    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in manager.getAllPlugins():
            if plugin.name == enabled_report.name:
                # If plugin_type isn't set, it can't be a report
                try:
                    plugin_type = plugin.plugin_object.plugin_type()
                except:
                    plugin_type = 'widget'
                if plugin_type == 'report':
                    data = {}
                    data['name'] = plugin.name
                    data['title'] = plugin.plugin_object.get_title()
                    reports.append(data)

                    break
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
            plugin_type != 'machine_info' and plugin_type != 'full_page':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'bu_dashboard', bu.id)

    c = {'user': request.user, 'machine_groups': machine_groups, 'is_editor': is_editor, 'business_unit': business_unit, 'user_level': user_level, 'output':output, 'reports':reports }
    return render(request, 'server/bu_dashboard.html', c)

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
        machine_groups = MachineGroup.objects.filter(business_unit=business_units).all()

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
                machines_unsorted = machines_unsorted | machine_group.machine_set.all().filter(deployed=True)
            #machines_unsorted = machines_unsorted | machine_group.machines.all()
        #machines = user.businessunit_set.select_related('machine_group_set').order_by('machine')
        all_machines = machines_unsorted
        if user_level == 'GA':
            business_units = BusinessUnit.objects.all()
            all_machines = Machine.deployed_objects.all()

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

    return render(request, 'server/overview_list_all.html', c)

@login_required
def delete_machine_group(request, group_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))

    machines = []
    # for machine_group in machine_groups:
    #     machines.append(machine_group.machine_set.all())

    machines = Machine.deployed_objects.filter(machine_group=machine_group)

    c = {'user': user, 'machine_group': machine_group, 'machines':machines}
    return render(request, 'server/machine_group_delete_confirm.html', c)

@login_required
def really_delete_machine_group(request, group_id):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))
    business_unit = machine_group.business_unit
    machine_group.delete()
    return redirect('bu_dashboard', business_unit.id)

# Machine Group Dashboard
@login_required
def group_dashboard(request, group_id):
    # check user is allowed to access this
    user = request.user
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
    machines = machine_group.machine_set.all().filter(deployed=True)
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    reports = []
    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in manager.getAllPlugins():
            if plugin.name == enabled_report.name:
                # If plugin_type isn't set, it can't be a report
                try:
                    plugin_type = plugin.plugin_object.plugin_type()
                except:
                    plugin_type = 'widget'
                if plugin_type == 'report':
                    data = {}
                    data['name'] = plugin.name
                    data['title'] = plugin.plugin_object.get_title()
                    reports.append(data)

                    break
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
            plugin_type != 'machine_info' and plugin_type != 'full_page':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'group_dashboard', machine_group.id)
    c = {'user': request.user, 'machine_group': machine_group, 'user_level': user_level,  'is_editor': is_editor, 'business_unit': business_unit, 'output':output, 'request':request, 'reports':reports}
    return render(request, 'server/group_dashboard.html', c)

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
    return render(request, 'forms/new_machine_group.html', c)

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
    return render(request, 'forms/edit_machine_group.html', c)

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
    return render(request, 'forms/new_machine.html', c)

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

    ip_address = None
    try:
        ip_address = machine.conditions.get(condition_name='ipv4_address')
        ip_address = ip_address.condition_data
    except (Condition.MultipleObjectsReturned, Condition.DoesNotExist):
        pass

    install_results = {}
    for result in report.get('InstallResults', []):
        nameAndVers = result['name'] + '-' + result['version']
        if result['status'] == 0:
            install_results[nameAndVers] = "installed"
        else:
            install_results[nameAndVers] = 'error'


    #if install_results:
    for item in report.get('ItemsToInstall', []):
        name = item.get('display_name', item['name'])
        nameAndVers = ('%s-%s'
            % (name, item['version_to_install']))
        item['install_result'] = install_results.get(
            nameAndVers, 'pending')

        # Get the update history
        try:
            update_history = UpdateHistory.objects.get(machine=machine,
            version=item['version_to_install'],
            name=item['name'], update_type='third_party')
        except IndexError, e:
            pass
        except UpdateHistory.DoesNotExist:
            pass

        try:
            item['update_history'] = UpdateHistoryItem.objects.filter(update_history=update_history)
        except:
            pass

    for item in report.get('ManagedInstalls', []):
        if 'version_to_install' in item:
            name = item.get('display_name', item['name'])
            nameAndVers = ('%s-%s'
                % (name, item['version_to_install']))
            if install_results.get(nameAndVers) == 'installed':
                item['installed'] = True

        if 'version_to_install' in item or 'installed_version' in item:
            if 'version_to_install' in item:
                version = item['version_to_install']
            else:
                version = item['installed_version']
            item['version'] = version
            # Get the update history
            try:
                update_history = UpdateHistory.objects.get(machine=machine,
                version=version,
                name=item['name'], update_type='third_party')
                item['update_history'] = UpdateHistoryItem.objects.filter(update_history=update_history)
            except Exception, e:
                pass


    # handle items that were removed during the most recent run
    # this is crappy. We should fix it in Munki.
    removal_results = {}
    for result in report.get('RemovalResults', []):
        try:
            m = re.search('^Removal of (.+): (.+)$', result)
        except:
            m = None
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

    uptime_enabled = False
    plugins = Plugin.objects.all()
    for plugin in plugins:
        if plugin.name == 'Uptime':
            uptime_enabled = True

    if uptime_enabled == True:
        try:
            plugin_script_submission = PluginScriptSubmission.objects.get(machine=machine, plugin__exact='Uptime')
            uptime_seconds = PluginScriptRow.objects.get(submission=plugin_script_submission, pluginscript_name__exact='UptimeSeconds').pluginscript_data
        except:
            uptime_seconds = '0'
    else:
        uptime_seconds=0

    uptime = utils.display_time(int(uptime_seconds))
    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()

    # Woo, plugin time
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
    enabled_plugins = MachineDetailPlugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            # If plugin_type isn't set, assume its an old style one
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
            plugin_type != 'builtin' and plugin_type != 'report':
                data = {}
                data['name'] = plugin.name
                data['html'] = '<div id="plugin-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, page="machine_detail")

    c = {'user':user, 'machine_group': machine_group, 'business_unit': business_unit, 'report': report, 'install_results': install_results, 'removal_results': removal_results, 'machine': machine, 'ip_address':ip_address, 'uptime_enabled':uptime_enabled, 'uptime':uptime,'output':output }
    return render(request, 'server/machine_detail.html', c)

@login_required
def machine_detail_facter(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    table_data = []
    if machine.facts.count() != 0:
        facts = machine.facts.all()
        if settings.EXCLUDED_FACTS:
            for excluded in settings.EXCLUDED_FACTS:
                facts = facts.exclude(fact_name=excluded)
    else:
        facts = None

    if facts:
        for fact in facts:
            item = {}
            item['key'] = fact.fact_name
            item['value'] = fact.fact_data
            table_data.append(item)
    key_header = 'Fact'
    value_header = 'Data'
    title = 'Facter data for %s' % machine.hostname
    c = {
        'user': request.user,
        'machine': machine,
        'table_data': table_data,
        'title': title,
        'key_header': key_header,
        'value_header': value_header
        }
    return render(request, 'server/machine_detail_table.html', c)

def machine_detail_conditions(request, machine_id):
    machine = get_object_or_404(Machine, pk=machine_id)
    table_data = []
    if machine.conditions.count() != 0:
        conditions = machine.conditions.all()
        if settings.EXCLUDED_CONDITIONS:
            for excluded in settings.EXCLUDED_CONDITIONS:
                conditions = conditions.exclude(condition_name=excluded)
    else:
        conditions = None

    if conditions:
        for condition in conditions:
            item = {}
            item['key'] = condition.condition_name
            item['value'] = condition.condition_data
            table_data.append(item)
    key_header = 'Condition'
    value_header = 'Data'
    title = 'Munki conditions data for %s' % machine.hostname
    c = {
        'user': request.user,
        'machine': machine,
        'table_data': table_data,
        'title': title,
        'key_header': key_header,
        'value_header': value_header
        }
    return render(request, 'server/machine_detail_table.html', c)


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

    try:
        senddata_setting = SalSetting.objects.get(name='send_data')
    except SalSetting.DoesNotExist:
        senddata_setting = SalSetting(name='send_data', value='yes')
        senddata_setting.save()

    c = {'user':request.user, 'request':request, 'historical_setting_form':historical_setting_form,'senddata_setting':senddata_setting.value}
    return render(request, 'server/settings.html', c)

@login_required
def senddata_enable(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    try:
        senddata_setting = SalSetting.objects.get(name='send_data')
    except SalSetting.DoesNotExist:
        senddata_setting = SalSetting(name='send_data', value='yes')
    senddata_setting.value = 'yes'
    senddata_setting.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@login_required
def senddata_disable(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    try:
        senddata_setting = SalSetting.objects.get(name='send_data')
    except SalSetting.DoesNotExist:
        senddata_setting = SalSetting(name='send_data', value='no')
    senddata_setting.value = 'no'
    senddata_setting.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
    disabled_plugins = utils.disabled_plugins(plugin_kind='main')
    c = {'user':request.user, 'request':request, 'enabled_plugins':enabled_plugins, 'disabled_plugins':disabled_plugins}
    return render(request, 'server/plugins.html', c)

@login_required
def settings_reports(request):
        user = request.user
        user_level = user.userprofile.level
        if user_level != 'GA':
            return redirect(index)
        # Load the plugins
        utils.reloadPluginsModel()
        enabled_plugins = Report.objects.all()
        disabled_plugins = utils.disabled_plugins(plugin_kind='report')
        c = {'user':request.user, 'request':request, 'enabled_plugins':enabled_plugins, 'disabled_plugins':disabled_plugins}
        return render(request, 'server/reports.html', c)

@login_required
def settings_machine_detail_plugins(request):
        user = request.user
        user_level = user.userprofile.level
        if user_level != 'GA':
            return redirect(index)
        # Load the plugins
        utils.reloadPluginsModel()
        enabled_plugins = MachineDetailPlugin.objects.all()
        disabled_plugins = utils.disabled_plugins(plugin_kind='machine_detail')
        c = {'user':request.user, 'request':request, 'enabled_plugins':enabled_plugins, 'disabled_plugins':disabled_plugins}
        return render(request, 'server/machine_detail_plugins.html', c)

@login_required
def plugin_plus(request, plugin_id):
    _swap_plugin(request, plugin_id, 1)
    return redirect('plugins_page')


@login_required
def plugin_minus(request, plugin_id):
    _swap_plugin(request, plugin_id, -1)
    return redirect('plugins_page')


def _swap_plugin(request, plugin_id, direction):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')

    # get current plugin order
    current_plugin = get_object_or_404(Plugin, pk=plugin_id)

	# Since it is sorted by order, we can swap the order attribute
    # of the selected plugin with the adjacent object in the queryset.

	# get all plugins (ordered by their order attribute).
    plugins = Plugin.objects.all()

    # Find the index in the query of the moving plugin.
    index = 0
    for plugin in plugins:
        if plugin.id == int(plugin_id):
            break
        index += 1

	# Perform the swap.
    temp_id = current_plugin.order
    current_plugin.order = plugins[index + direction].order
    current_plugin.save()
    plugins[index + direction].order = temp_id
    plugins[index + direction].save()


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
def machine_detail_plugin_plus(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')

    # get current plugin order
    current_plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)

    # get 'old' next one
    old_plugin = get_object_or_404(Plugin, order=(int(current_plugin.order)+1))
    current_plugin.order = current_plugin.order + 1
    current_plugin.save()

    old_plugin.order = old_plugin.order - 1
    old_plugin.save()
    return redirect('settings_machine_detail_plugins')

@login_required
def machine_detail_plugin_minus(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')

    # get current plugin order
    current_plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)
    #print current_plugin
    # get 'old' previous one

    old_plugin = get_object_or_404(MachineDetailPlugin, order=(int(current_plugin.order)-1))
    current_plugin.order = current_plugin.order - 1
    current_plugin.save()

    old_plugin.order = old_plugin.order + 1
    old_plugin.save()
    return redirect('settings_machine_detail_plugins')

@login_required
def machine_detail_plugin_disable(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')
    plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)
    plugin.delete()
    return redirect('settings_machine_detail_plugins')

@login_required
def machine_detail_plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = MachineDetailPlugin(name=plugin_name, order=utils.UniquePluginOrder(plugin_type='machine_detail'))
        plugin.save()
    return redirect('settings_machine_detail_plugins')

@login_required
def settings_report_disable(request, plugin_id):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    user_level = profile.level
    if user_level != 'GA':
        return redirect('server.views.index')
    plugin = get_object_or_404(Report, pk=plugin_id)
    plugin.delete()
    return redirect('settings_reports')

@login_required
def settings_report_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Report.objects.get(name=plugin_name)
    except Report.DoesNotExist:
        plugin = Report(name=plugin_name)
        plugin.save()
    return redirect('settings_reports')

@login_required
def api_keys(request):
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)

    api_keys = ApiKey.objects.all()
    c = {'user':request.user, 'api_keys':api_keys, 'request':request}
    return render(request, 'server/api_keys.html', c)

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
    return render(request, 'forms/new_api_key.html', c)

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
        return render(request, 'server/api_key_display.html', c)

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
    return render(request, 'forms/edit_api_key.html', c)

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
@key_auth_required
def preflight(request):
    # osquery plugins aren't a thing anymore.
    # This is just to stop old clients from barfing.
    output = {}
    output['queries'] = {}

    return HttpResponse(json.dumps(output))

# It's the new preflight (woo)
@csrf_exempt
@key_auth_required
def preflight_v2(request):
    # find plugins that have embedded preflight scripts
    # Load in the default plugins if needed
    utils.loadDefaultPlugins()
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in manager.getAllPlugins():
            if enabled_report.name == plugin.name:
                content = utils.get_plugin_scripts(plugin, hash_only=True)
                if content:
                    output.append(content)

                break
    enabled_machine_detail_plugins = MachineDetailPlugin.objects.all()
    # print enabled_machine_detail_plugins
    for enabled_machine_detail_plugin in enabled_machine_detail_plugins:
        for plugin in manager.getAllPlugins():
            if enabled_machine_detail_plugin.name == plugin.name:
                content = utils.get_plugin_scripts(plugin, hash_only=True)
                if content:
                    output.append(content)

                break
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all()
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            if plugin.name == enabled_plugin.name:
                content = utils.get_plugin_scripts(plugin, hash_only=True)
                if content:
                    output.append(content)
                break

    return HttpResponse(json.dumps(output))

# Get script for plugin
@csrf_exempt
@key_auth_required
def preflight_v2_get_script(request, pluginName, scriptName):
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []
    for plugin in manager.getAllPlugins():
        if plugin.name == pluginName:
            content = utils.get_plugin_scripts(plugin, hash_only=False, script_name=scriptName)
            if content:
                output.append(content)
            break
    return HttpResponse(json.dumps(output))
# checkin
@csrf_exempt
@key_auth_required
def checkin(request):
    if request.method != 'POST':
        print 'not post data'
        return HttpResponseNotFound('No POST data sent')

    data = request.POST
    key = data.get('key')
    uuid = data.get('uuid')
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

    try:
        deployed_on_checkin = settings.DEPLOYED_ON_CHECKIN
    except:
        deployed_on_checkin = True

    if key is None or key == 'None':
        try:
            key = settings.DEFAULT_MACHINE_GROUP_KEY
        except Exception:
            pass

    machine_group = get_object_or_404(MachineGroup, key=key)
    machine.machine_group = machine_group
    business_unit = machine_group.business_unit
    try:
        historical_setting = SalSetting.objects.get(name='historical_retention')
        historical_days = historical_setting.value
    except SalSetting.DoesNotExist:
        historical_setting = SalSetting(name='historical_retention', value='180')
        historical_setting.save()
        historical_days = '180'

    machine.hostname = data.get('name', '<NO NAME>')
    machine.last_checkin = django.utils.timezone.now()
    if 'username' in data:
        if data.get('username') != '_mbsetupuser':
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

    if not machine.machine_model_friendly:
        try:
            machine.machine_model_friendly = utils.friendly_machine_model(machine)
        except:
            machine.machine_model_friendly = machine.machine_model

    if deployed_on_checkin is True:
        machine.deployed = True

    machine.save()

    # If Plugin_Results are in the report, handle them
    try:
        datelimit = django.utils.timezone.now() - timedelta(days=historical_days)
        PluginScriptSubmission.objects.filter(recorded__lt=datelimit).delete()
    except:
        pass

    if 'Plugin_Results' in report_data:
        utils.process_plugin_script(report_data.get('Plugin_Results'), machine)

    # Remove existing PendingUpdates for the machine
    updates = machine.pending_updates.all().delete()
    now = django.utils.timezone.now()
    if 'ItemsToInstall' in report_data:
        pending_update_to_save = []
        update_history_item_to_save = []
        for update in report_data.get('ItemsToInstall'):
            display_name = update.get('display_name', update['name'])
            update_name = update.get('name')
            version = str(update['version_to_install'])
            if version:
                pending_update = PendingUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                if IS_POSTGRES:
                    pending_update_to_save.append(pending_update)
                else:
                    pending_update.save()
                # Let's handle some of those lovely pending installs into the UpdateHistory Model
                try:
                    update_history = UpdateHistory.objects.get(name=update_name,
                    version=version, machine=machine, update_type='third_party')
                except UpdateHistory.DoesNotExist:
                    update_history = UpdateHistory(name=update_name, version=version, machine=machine, update_type='third_party')
                    update_history.save()

                if update_history.pending_recorded == False:
                    update_history_item = UpdateHistoryItem(
                        update_history=update_history, status='pending',
                        recorded=now, uuid=uuid)

                    update_history.pending_recorded = True
                    update_history.save()

                    if IS_POSTGRES:
                        update_history_item_to_save.append(update_history_item)
                    else:
                        update_history_item.save()

        if IS_POSTGRES:
            PendingUpdate.objects.bulk_create(pending_update_to_save)
            UpdateHistoryItem.objects.bulk_create(update_history_item_to_save)

    updates = machine.installed_updates.all().delete()

    if 'ManagedInstalls' in report_data:
        installed_updates_to_save = []
        for update in report_data.get('ManagedInstalls'):
            display_name = update.get('display_name', update['name'])
            update_name = update.get('name')
            version = str(update.get('installed_version', 'UNKNOWN'))
            installed = update.get('installed')
            if version != 'UNKNOWN' and version != None and len(version) != 0:
                installed_update = InstalledUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name, installed=installed)
                if IS_POSTGRES:
                    installed_updates_to_save.append(installed_update)
                else:
                    installed_update.save()
        if IS_POSTGRES:
            InstalledUpdate.objects.bulk_create(installed_updates_to_save)

    # Remove existing PendingAppleUpdates for the machine
    updates = machine.pending_apple_updates.all().delete()
    if 'AppleUpdates' in report_data:
        for update in report_data.get('AppleUpdates'):
            display_name = update.get('display_name', update['name'])
            update_name = update.get('name')
            version = str(update['version_to_install'])
            try:
                pending_update = PendingAppleUpdate.objects.get(machine=machine, display_name=display_name, update_version=version, update=update_name)
            except PendingAppleUpdate.DoesNotExist:
                pending_update = PendingAppleUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()
            # Let's handle some of those lovely pending installs into the UpdateHistory Model
            try:
                update_history = UpdateHistory.objects.get(name=update_name, version=version, machine=machine, update_type='apple')
            except UpdateHistory.DoesNotExist:
                update_history = UpdateHistory(name=update_name, version=version, machine=machine, update_type='apple')
                update_history.save()

            if update_history.pending_recorded == False:
                update_history_item = UpdateHistoryItem(update_history=update_history, status='pending', recorded=now, uuid=uuid)
                update_history_item.save()
                update_history.pending_recorded = True
                update_history.save()



    # if Facter data is submitted, we need to first remove any existing facts for this machine
    if IS_POSTGRES:
        # If we are using postgres, we can just dump them all and do a bulk create
        if 'Facter' in report_data:
            facts = machine.facts.all().delete()
            try:
                datelimit = django.utils.timezone.now() - timedelta(days=historical_days)
                HistoricalFact.objects.filter(fact_recorded__lt=datelimit).delete()
            except Exception:
                pass
            try:
                historical_facts = settings.HISTORICAL_FACTS
            except Exception:
                historical_facts = []
                pass

            facts_to_be_created = []
            historical_facts_to_be_created = []
            for fact_name, fact_data in report_data['Facter'].iteritems():
                skip = False
                if hasattr(settings, 'IGNORE_FACTS'):
                    for prefix in settings.IGNORE_FACTS:
                        if fact_name.startswith(prefix):
                            skip = True
                if skip == True:
                    continue
                facts_to_be_created.append(
                            Fact(
                                machine=machine,
                                fact_data=fact_data,
                                fact_name=fact_name
                                )
                            )
                if fact_name in historical_facts:
                    historical_facts_to_be_created.append(
                        HistoricalFact(
                            machine=machine,
                            fact_data=fact_data,
                            fact_name=fact_name
                            )
                    )
            Fact.objects.bulk_create(facts_to_be_created)
            if len(historical_facts_to_be_created) != 0:
                HistoricalFact.objects.bulk_create(historical_facts_to_be_created)

    else:
        if 'Facter' in report_data:
            facts = machine.facts.all()
            for fact in facts:
                skip = False
                if hasattr(settings, 'IGNORE_FACTS'):
                    for prefix in settings.IGNORE_FACTS:

                        if fact.fact_name.startswith(prefix):
                            skip = True
                            fact.delete()
                            break
                if skip == False:
                    continue
                found = False
                for fact_name, fact_data in report_data['Facter'].iteritems():

                    if fact.fact_name == fact_name:
                        found = True
                        break
                if found == False:
                    fact.delete()

            # Delete old historical facts

            try:
                datelimit = django.utils.timezone.now() - timedelta(days=historical_days)
                HistoricalFact.objects.filter(fact_recorded__lt=datelimit).delete()
            except Exception:
                pass
            try:
                historical_facts = settings.HISTORICAL_FACTS
            except Exception:
                historical_facts = []
                pass
            # now we need to loop over the submitted facts and save them
            facts = machine.facts.all()
            for fact_name, fact_data in report_data['Facter'].iteritems():

                # does fact exist already?
                found = False
                skip = False
                if hasattr(settings, 'IGNORE_FACTS'):
                    for prefix in settings.IGNORE_FACTS:

                        if fact_name.startswith(prefix):
                            skip = True
                            break
                if skip == True:
                    continue
                for fact in facts:
                    if fact_name == fact.fact_name:
                        # it exists, make sure it's got the right info
                        found = True
                        if fact_data == fact.fact_data:
                            # it's right, break
                            break
                        else:
                            fact.fact_data = fact_data
                            fact.save()
                            break
                if found == False:

                    fact = Fact(machine=machine, fact_data=fact_data, fact_name=fact_name)
                    fact.save()

                if fact_name in historical_facts:
                    fact = HistoricalFact(machine=machine, fact_name=fact_name, fact_data=fact_data, fact_recorded=datetime.now())
                    fact.save()

    if IS_POSTGRES:
        if 'Conditions' in report_data:
            machine.conditions.all().delete()
            conditions_to_be_created = []
            for condition_name, condition_data in report_data['Conditions'].iteritems():
                # Skip the conditions that come from facter
                if 'Facter' in report_data and condition_name.startswith('facter_'):
                    continue

                condition_data = utils.listify_condition_data(condition_data)
                conditions_to_be_created.append(
                    Condition(
                        machine=machine,
                        condition_name=condition_name,
                        condition_data=utils.safe_unicode(condition_data)
                    )
                )

            Condition.objects.bulk_create(conditions_to_be_created)
    else:
        if 'Conditions' in report_data:
            conditions = machine.conditions.all()
            for condition in conditions:
                found = False
                for condition_name, condition_data in report_data['Conditions'].iteritems():
                    if condition.condition_name == condition_name:
                        found = True
                        break
                if found == False:
                    condition.delete()

            conditions = machine.conditions.all()
            for condition_name, condition_data in report_data['Conditions'].iteritems():
                # Skip the conditions that come from facter
                if 'Facter' in report_data and condition_name.startswith('facter_'):
                    continue

                # if it's a list (more than one result), we're going to conacetnate it into one comma separated string
                condition_data = utils.listify_condition_data(condition_data)

                found = False
                for condition in conditions:
                    if condition_name == condition.condition_name:
                        # it exists, make sure it's got the right info
                        found = True
                        if condition_data == condition.condition_data:
                            # it's right, break
                            break
                        else:
                            condition.condition_data = condition_data
                            condition.save()
                            break
                if found == False:
                    condition = Condition(machine=machine, condition_name=condition_name, condition_data=utils.safe_unicode(condition_data))
                    condition.save()

    utils.run_plugin_processing(machine, report_data)
    utils.get_version_number()
    return HttpResponse("Sal report submmitted for %s"
                        % data.get('name'))

@csrf_exempt
@key_auth_required
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

def process_update_item(name, version, update_type, action, recorded, machine, uuid, extra=None):
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
        update_history=update_history
        )
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
            # Make sure there has't been a pending in the same sal run
            # Remove them if there are
            remove_items = UpdateHistoryItem.objects.filter(uuid=uuid,
            status='pending', update_history=update_history)
            remove_items.delete()
            update_history.pending_recorded = False
            update_history.save()

@csrf_exempt
@key_auth_required
def install_log_submit(request):
    if request.method != 'POST':
        return HttpResponseNotFound('No POST data sent')


    submission = request.POST
    serial = submission.get('serial')
    key = submission.get('key')
    uuid = submission.get('run_uuid')
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            return HttpResponseNotFound('Machine not found')

        # Check the key
        machine_group = get_object_or_404(MachineGroup, key=key)
        if machine_group.id != machine.machine_group.id:
            return HttpResponseNotFound('No machine group found')

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
                            machine, uuid)
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
                        machine, uuid, extra)
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
                            #(name, version) = m.group(2).rsplit('-',1)
                            name = m.group(2)
                            version = ''
                            process_update_item(name, version, 'third_party', 'removal', the_date,
                            machine, uuid)
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
                        machine, uuid, extra)
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
                            machine, uuid)
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
                        machine, uuid, extra)
                        # We've processed this line, move on
                        continue

                    except IndexError:
                        pass
            machine.install_log_hash = \
                hashlib.sha256(log_str).hexdigest()
            machine.install_log = log_str
            machine.save()
        return HttpResponse("Install Log processed for %s" % serial)
