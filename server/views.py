import os
import re
from datetime import timedelta

from yapsy.PluginManager import PluginManager

import django.utils.timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf

import utils
from forms import *
from inventory.models import *
from models import *
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
        # The first user created by syncdb won't have a profile. If there isn't
        # one, make sure they get one.
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=user)

        profile.level = 'GA'
        profile.save()
    user_level = user.userprofile.level

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

    # TODO: Plugin code smell
    # Load in the default plugins if needed
    utils.load_default_plugins()
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
        settings.PROJECT_DIR, 'server/plugins')])
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
                except Exception:
                    plugin_type = 'widget'
                if plugin_type == 'report':
                    data = {}
                    data['name'] = plugin.name
                    data['title'] = plugin.plugin_object.get_title()
                    reports.append(data)

                    break
    # TODO: Plugin code smell
    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            # If plugin_type isn't set, assume its an old style one
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except Exception:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
                    plugin_type != 'machine_info' and plugin_type != 'report':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))  # noqa: E501
                output.append(data)
                break

    output = utils.orderPluginOutput(output)

    # If the user is GA level, and hasn't decided on a data sending
    # choice, template will reflect this.
    data_choice = False if (user_level == 'GA' and utils.get_setting('send_data') is None) else True

    # get the user level - if they're a global admin, show all of the
    # machines. If not, show only the machines they have access to
    if user_level == 'GA':
        business_units = BusinessUnit.objects.all()
    else:
        business_units = user.businessunit_set.all()

    context = {
        'user': request.user,
        'business_units': business_units,
        'output': output,
        'data_setting_decided': data_choice,
        'reports': reports}

    context.update(utils.check_version())

    return render(request, 'server/index.html', context)


@login_required
def machine_list(request, pluginName, data, page='front', theID=None):
    (machines, title) = utils.plugin_machines(
        request, pluginName, data, page, theID, get_machines=False)
    user = request.user
    page_length = utils.get_setting('datatable_page_length')
    c = {'user': user, 'plugin_name': pluginName, 'machines': machines, 'req_type': page,
         'title': title, 'bu_id': theID, 'request': request, 'data': data,
         'page_length': page_length}

    return render(request, 'server/overview_list_all.html', c)


@login_required
@ga_required
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
    return render(request, 'forms/new_business_unit.html', c)


@login_required
@ga_required
def edit_business_unit(request, bu_id):
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        if request.user.is_staff:
            form = EditUserBusinessUnitForm(request.POST, instance=business_unit)
        else:
            form = EditBusinessUnitForm(request.POST, instance=business_unit)
        if form.is_valid():
            new_business_unit = form.save(commit=False)
            new_business_unit.save()
            form.save_m2m()
            return redirect('bu_dashboard', new_business_unit.id)
    else:
        if request.user.is_staff:
            form = EditUserBusinessUnitForm(instance=business_unit)
        else:
            form = EditBusinessUnitForm(instance=business_unit)
    c = {'form': form, 'business_unit': business_unit}
    return render(request, 'forms/edit_business_unit.html', c)


@login_required
@ga_required
def delete_business_unit(request, bu_id):
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))

    machine_groups = business_unit.machinegroup_set.all()
    machines = []

    machines = Machine.deployed_objects.filter(machine_group__business_unit=business_unit)

    c = {'user': request.user, 'business_unit': business_unit,
         'machine_groups': machine_groups, 'machines': machines}
    return render(request, 'server/business_unit_delete_confirm.html', c)


@login_required
@ga_required
def really_delete_business_unit(request, bu_id):
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    business_unit.delete()
    return redirect(index)


@login_required
@access_required(BusinessUnit)
def bu_dashboard(request, **kwargs):
    business_unit = kwargs['business_unit']
    machine_groups = business_unit.machinegroup_set.all()

    # TODO: Busted! Code smell
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
        settings.PROJECT_DIR, 'server/plugins')])
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
                except Exception:
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
            except Exception:
                plugin_type = 'widget'
            if plugin.name == enabled_plugin.name and \
                    plugin_type != 'machine_info' and plugin_type != 'full_page':
                data = {}
                data['name'] = plugin.name
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = '<div id="plugin-%s" class="col-md-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], str(data['width']), static('img/blue-spinner.gif'))  # noqa: E501
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'bu_dashboard', business_unit.id)

    context = {
        'user': request.user,
        'machine_groups': machine_groups,
        'business_unit': business_unit,
        'user_level': request.user.userprofile.level,
        'output': output,
        'reports': reports}
    return render(request, 'server/bu_dashboard.html', context)


@login_required
@ga_required
def delete_machine_group(request, group_id):
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))

    machines = []
    # for machine_group in machine_groups:
    #     machines.append(machine_group.machine_set.all())

    machines = Machine.deployed_objects.filter(machine_group=machine_group)

    c = {'user': request.user, 'machine_group': machine_group, 'machines': machines}
    return render(request, 'server/machine_group_delete_confirm.html', c)


@login_required
@ga_required
def really_delete_machine_group(request, group_id):
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))
    business_unit = machine_group.business_unit
    machine_group.delete()
    return redirect('bu_dashboard', business_unit.id)


@login_required
@access_required(MachineGroup)
def group_dashboard(request, **kwargs):
    machine_group = kwargs['instance']
    machines = machine_group.machine_set.all().filter(deployed=True)  # noqa: F841

    all_plugins = utils.get_all_plugins()

    # TODO: Code smell
    output = []
    reports = []
    for enabled_report in Report.objects.all():
        for plugin in all_plugins:
            if plugin.name == enabled_report.name:
                # If plugin_type isn't set, it can't be a report
                try:
                    plugin_type = plugin.plugin_object.plugin_type()
                except Exception:
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
        for plugin in all_plugins:
            try:
                p_type = plugin.plugin_object.plugin_type()
            except Exception:
                p_type = 'widget'

            if plugin.name == enabled_plugin.name and p_type not in ('machine_info', 'full_page'):
                data = {'name': plugin.name}
                data['width'] = plugin.plugin_object.widget_width()
                data['html'] = (
                    '<div id="plugin-%s" class="col-md-%s">'
                    '<img class="center-block blue-spinner" src="%s"/></div>') % (
                        data['name'], str(data['width']), static('img/blue-spinner.gif'))
                output.append(data)
                break

    output = utils.orderPluginOutput(output, 'group_dashboard', machine_group.id)
    context = {
        'user': request.user,
        'machine_group': machine_group,
        'user_level': request.user.userprofile.level,
        'business_unit': kwargs['business_unit'],
        'output': output,
        'request': request,
        'reports': reports}
    return render(request, 'server/group_dashboard.html', context)


@login_required
@required_level(ProfileLevel.global_admin, ProfileLevel.read_write)
@access_required(BusinessUnit)
def new_machine_group(request, bu_id, **kwargs):
    business_unit = kwargs['business_unit']

    if request.method == 'POST':
        form = MachineGroupForm(request.POST)
        if form.is_valid():
            new_machine_group = form.save(commit=False)
            new_machine_group.business_unit = business_unit
            new_machine_group.save()
            return redirect('group_dashboard', new_machine_group.id)
    else:
        form = MachineGroupForm()

    context = {'form': form, 'business_unit': business_unit}
    return render(request, 'forms/new_machine_group.html', context)


@login_required
@required_level(ProfileLevel.global_admin, ProfileLevel.read_write)
@access_required(MachineGroup)
def edit_machine_group(request, group_id, **kwargs):
    machine_group = kwargs['instance']
    if request.method == 'POST':
        form = EditMachineGroupForm(request.POST, instance=machine_group)
        if form.is_valid():
            machine_group.save()
            return redirect('group_dashboard', machine_group.id)
    else:
        form = EditMachineGroupForm(instance=machine_group)

    context = {'form': form, 'business_unit': kwargs['business_unit'], 'machine_group':
               machine_group}
    return render(request, 'forms/edit_machine_group.html', context)


@login_required
@required_level(ProfileLevel.global_admin, ProfileLevel.read_write)
@access_required(MachineGroup)
def new_machine(request, group_id, **kwargs):
    machine_group = kwargs['instance']
    if request.method == 'POST':
        form = NewMachineForm(request.POST)
        if form.is_valid():
            new_machine = form.save(commit=False)
            new_machine.machine_group = machine_group
            new_machine.save()
            return redirect('machine_detail', new_machine.id)
    else:
        form = NewMachineForm()

    context = {'form': form, 'machine_group': machine_group}
    return render(request, 'forms/new_machine.html', context)


@login_required
@access_required(Machine)
def machine_detail(request, **kwargs):
    machine = kwargs['instance']
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit

    report = machine.get_report()

    try:
        ip_address_condition = machine.conditions.get(condition_name='ipv4_address')
        ip_address = ip_address_condition.condition_data
    except (Condition.MultipleObjectsReturned, Condition.DoesNotExist):
        ip_address = None

    install_results = {}
    for result in report.get('InstallResults', []):
        nameAndVers = result['name'] + '-' + result['version']
        if result['status'] == 0:
            install_results[nameAndVers] = "installed"
        else:
            install_results[nameAndVers] = 'error'

    # if install_results:
    for item in report.get('ItemsToInstall', []):
        name = item.get('display_name', item['name'])
        nameAndVers = ('%s-%s'
                       % (name, item['version_to_install']))
        item['install_result'] = install_results.get(
            nameAndVers, 'pending')

        # Get the update history
        try:
            item['update_history'] = UpdateHistory.objects.get(
                machine=machine, version=item['version_to_install'], name=item['name'],
                update_type='third_party').updatehistoryitem_set.all()
        except (IndexError, UpdateHistory.DoesNotExist):
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
                item['update_history'] = UpdateHistory.objects.get(
                    machine=machine, version=version, name=item['name'],
                    update_type='third_party').updatehistoryitem_set.all()
            except Exception:
                pass

    # handle items that were removed during the most recent run
    # this is crappy. We should fix it in Munki.
    removal_results = {}
    for result in report.get('RemovalResults', []):
        try:
            m = re.search('^Removal of (.+): (.+)$', result)
        except Exception:
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
                if 'RemovedItems' not in report:
                    report['RemovedItems'] = [item['name']]
                elif name not in report['RemovedItems']:
                    report['RemovedItems'].append(item['name'])

    uptime_enabled = False
    plugins = Plugin.objects.all()
    for plugin in plugins:
        if plugin.name == 'Uptime':
            uptime_enabled = True

    if uptime_enabled:
        try:
            plugin_script_submission = PluginScriptSubmission.objects.get(
                machine=machine, plugin__exact='Uptime')
            uptime_seconds = PluginScriptRow.objects.get(
                submission=plugin_script_submission,
                pluginscript_name__exact='UptimeSeconds').pluginscript_data
        except Exception:
            uptime_seconds = '0'
    else:
        uptime_seconds = 0

    uptime = utils.display_time(int(uptime_seconds))
    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()

    # TODO: Plugin code smell
    # Woo, plugin time
    # Load in the default plugins if needed
    utils.load_default_plugins()
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
        settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    output = []

    # TODO: Plugin code smell
    # Get all the enabled plugins
    enabled_plugins = MachineDetailPlugin.objects.all().order_by('order')
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in manager.getAllPlugins():
            # If plugin_type isn't set, assume its an old style one
            try:
                plugin_type = plugin.plugin_object.plugin_type()
            except Exception:
                plugin_type = 'widget'

            # If we can't get supported OS Families, assume it's for all
            try:
                supported_os_families = plugin.plugin_object.supported_os_families()
            except Exception:
                supported_os_families = ['Darwin', 'Windows', 'Linux', 'ChromeOS']
            if plugin.name == enabled_plugin.name and \
                    plugin_type not in ('builtin', 'report') and \
                    machine.os_family in supported_os_families:
                data = {'name': plugin.name}
                data['html'] = '<div id="plugin-%s"><img class="center-block blue-spinner" src="%s"/></div>' % (data['name'], static('img/blue-spinner.gif'))  # noqa: E501
                output.append(data)
                break

    output = utils.orderPluginOutput(output, page="machine_detail")

    context = {
        'user': request.user,
        'machine_group': machine_group,
        'business_unit': business_unit,
        'report': report,
        'install_results': install_results,
        'removal_results': removal_results,
        'machine': machine,
        'ip_address': ip_address,
        'uptime_enabled': uptime_enabled,
        'uptime': uptime,
        'output': output}
    return render(request, 'server/machine_detail.html', context)


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


@login_required
@access_required(Machine)
def delete_machine(request, **kwargs):
    machine = kwargs['instance']
    machine_group_id = machine.machine_group.id
    machine.delete()
    return redirect('group_dashboard', machine_group_id)

