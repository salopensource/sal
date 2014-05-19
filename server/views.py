# Create your views here.
from models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from datetime import datetime, timedelta, date
from django.db.models import Count
from django.contrib import messages
import plistlib
import ast
from forms import *
import pprint
import re
import os
from yapsy.PluginManager import PluginManager
import utils

# import logging
# logging.basicConfig(level=logging.DEBUG)

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
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    if user_level != 'GA':
        # user has many BU's display them all in a friendly manner
        business_units = user.businessunit_set.all()
        if user.businessunit_set.count() == 1:
            # user only has one BU, redirect to it
            for bu in user.businessunit_set.all():
                return redirect('server.views.bu_dashboard', bu_id=bu.id)
                break
    else:
        machines = Machine.objects.all()
        # Build the manager
        manager = PluginManager()
        # Tell it the default place(s) where to find plugins
        manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(settings.PROJECT_DIR, 'server/plugins')])
        # Load all plugins
        manager.collectPlugins()
        output = []
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            data = {}
            data['name'] = plugin.name
            (data['html'], data['width']) = plugin.plugin_object.show_widget('front', machines)
            #output.append(plugin.plugin_object.show_widget('front'))
            output.append(data)
        output = utils.orderPluginOutput(output)

        # get the user level - if they're a global admin, show all of the machines. If not, show only the machines they have access to
        business_units = BusinessUnit.objects.all()
        config_installed = 'config' in settings.INSTALLED_APPS

        c = {'user': request.user, 'business_units': business_units, 'output': output, 'config_installed': config_installed}
        return render_to_response('server/index.html', c, context_instance=RequestContext(request))

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
        machines = Machine.objects.all()

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
    c = {'user':user, 'machines': machines, 'req_type': page, 'title': title, 'bu_id': theID }

    return render_to_response('server/overview_list_all.html', c, context_instance=RequestContext(request))

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
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
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

    # Loop round the plugins and print their names.
    for plugin in manager.getAllPlugins():
        data = {}
        data['name'] = plugin.name
        (data['html'], data['width']) = plugin.plugin_object.show_widget('bu_dashboard', machines, bu.id)
        output.append(data)
    output = utils.orderPluginOutput(output, 'bu_dashboard', bu.id)

    c = {'user': request.user, 'machine_groups': machine_groups, 'is_editor': is_editor, 'business_unit': business_unit, 'user_level': user_level, 'output':output }
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
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
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
    for plugin in manager.getAllPlugins():
        data = {}
        data['name'] = plugin.name
        (data['html'], data['width']) = plugin.plugin_object.show_widget('group_dashboard', machines, machine_group.id)
        output.append(data)
    output = utils.orderPluginOutput(output, 'group_dashboard', machine_group.id)
    c = {'user': request.user, 'machine_group': machine_group, 'user_level': user_level,  'is_editor': is_editor, 'business_unit': business_unit, 'output':output}
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
        return redirect(index)
    c = {'form': form, 'is_editor': is_editor, 'business_unit': business_unit, }
    return render_to_response('forms/new_machine_group.html', c, context_instance=RequestContext(request))

# Edit Group

# Delete Group

# Machine detail
@login_required
def machine_detail(request, machine_id):
    # check the user is in a BU that's allowed to see this Machine
    machine = get_object_or_404(Machine, pk=machine_id)
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit
    user = request.user
    user_level = user.userprofile.level
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)

    report = machine.get_report()
    if machine.fact_set.count() != 0:
        facts = machine.fact_set.all()
        if settings.EXCLUDED_FACTS:
            for excluded in settings.EXCLUDED_FACTS:
                facts = facts.exclude(fact_name=excluded)
    else:
        facts = None

    if machine.condition_set.count() != 0:
        conditions = machine.condition_set.all()
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

    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()
    config_installed = 'config' in settings.INSTALLED_APPS
    c = {'user':user, 'machine_group': machine_group, 'business_unit': business_unit, 'report': report, 'install_results': install_results, 'removal_results': removal_results, 'machine': machine, 'facts':facts, 'conditions':conditions, 'ip_address':ip_address, 'config_installed':config_installed }
    return render_to_response('server/machine_detail.html', c, context_instance=RequestContext(request))

# checkin
@csrf_exempt
def checkin(request):
    if request.method != 'POST':
        print 'not post data'
        raise Http404

    data = request.POST
    key = data.get('key')
    serial = data.get('serial')

    if key is None or key == 'None':
        try:
            key = settings.DEFAULT_MACHINE_GROUP_KEY
        except Exception:
            pass

    machine_group = get_object_or_404(MachineGroup, key=key)

    business_unit = machine_group.business_unit

    # look for serial number - if it doesn't exist, create one
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            machine = Machine(serial=serial)
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

        # extract machine data from the report
        report_data = machine.get_report()
        # find the matching group based on manifest
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
            machine.last_puppet_run = datetime.fromtimestamp(float(puppet['time']['last_run']))
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
        updates = machine.pendingupdate_set.all()
        updates.delete()
        if 'ItemsToInstall' in report_data:
            for update in report_data.get('ItemsToInstall'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()

        # Remove existing PendingAppleUpdates for the machine
        updates = machine.pendingappleupdate_set.all()
        updates.delete()
        if 'AppleUpdates' in report_data:
            for update in report_data.get('AppleUpdates'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingAppleUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()

        # if Facter data is submitted, we need to first remove any existing facts for this machine
        if 'Facter' in report_data:
            facts = machine.fact_set.all()
            facts.delete()
            # Delete old historical facts
            try:
              historical_days = settings.HISTORICAL_DAYS
            except:
              historical_days = 180

            try:
                datelimit = datetime.now() - timedelta(days=historical_days)
                HistoricalFact.objects.filter(machine=machine, fact_recorded__lt=datelimit).delete()
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
            conditions = machine.condition_set.all()
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

        return HttpResponse("Sal report submmitted for %s.\n"
                            % data.get('name'))
