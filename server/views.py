import json
import re
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf

import sal.plugin
from sal.decorators import required_level, ProfileLevel, access_required, is_global_admin
from server.forms import (BusinessUnitForm, EditUserBusinessUnitForm, EditBusinessUnitForm,
                          MachineGroupForm, EditMachineGroupForm, NewMachineForm)
from server.models import (BusinessUnit, MachineGroup, Machine, UserProfile, Report, Condition,
                           UpdateHistory, Plugin, PluginScriptSubmission, PluginScriptRow,
                           ManagedItem)
from server.non_ui_views import process_plugin
from server import utils

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = utils.is_postgres()

# Bootstrap button classes for managed item statuses.
STATUSES = {
    'PRESENT': 'btn-success',
    'ABSENT': 'btn-danger',
    'PENDING': 'btn-info',
    'ERROR': 'btn-danger',
    'UNKNOWN': 'btn-default',}


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

        profile.level = ProfileLevel.global_admin
        profile.save()

    user_is_ga = is_global_admin(user)

    if not user_is_ga:
        # user has many BU's display them all in a friendly manner
        if user.businessunit_set.count() == 0:
            c = {'user': request.user, }
            return render(request, 'server/no_access.html', c)
        if user.businessunit_set.count() == 1:
            # user only has one BU, redirect to it
            return redirect('bu_dashboard', bu_id=user.businessunit_set.all()[0].id)

    # Load in the default plugins if needed
    utils.load_default_plugins()
    plugins = sal.plugin.PluginManager().get_all_plugins()

    reports = utils.get_report_names(plugins)
    output = utils.get_plugin_placeholder_markup(plugins)

    # If the user is GA level, and hasn't decided on a data sending
    # choice, template will reflect this.
    data_choice = False if (user_is_ga and utils.get_setting('send_data') is None) else True

    # get the user level - if they're a global admin, show all of the
    # machines. If not, show only the machines they have access to
    if user_is_ga:
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
def machine_list(request, plugin_name, data, group_type='all', group_id=None):
    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    # queryset = plugin_object.get_queryset(request, group_type=group_type, group_id=group_id)
    # Plugin will raise 404 if bad `data` is passed.
    machines, title = plugin_object.filter_machines(Machine.objects.none(), data)
    context = {
        'group_type': group_type,
        'group_id': group_id,
        'plugin_name': plugin_name,
        'machines': machines,
        'title': title,
        'request': request,
        'data': data,
        'page_length': utils.get_setting('datatable_page_length')}

    return render(request, 'server/overview_list_all.html', context)


@login_required
def report_load(request, plugin_name, group_type='all', group_id=None):
    groups = utils.get_instance_and_groups(group_type, group_id)
    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    report_html = plugin_object.widget_content(request, group_type=group_type, group_id=group_id)
    reports = Report.objects.values_list('name', flat=True)
    context = {'output': report_html, 'group_type': group_type, 'group_id': group_id, 'reports':
               reports, 'active_report': plugin_object, 'groups': groups}
    return render(request, 'server/display_report.html', context)


@login_required
@required_level(ProfileLevel.global_admin)
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
@required_level(ProfileLevel.global_admin)
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
@required_level(ProfileLevel.global_admin)
def delete_business_unit(request, bu_id):
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))

    machine_groups = business_unit.machinegroup_set.all()
    machines = []

    machines = Machine.deployed_objects.filter(machine_group__business_unit=business_unit)

    c = {'user': request.user, 'business_unit': business_unit,
         'machine_groups': machine_groups, 'machines': machines}
    return render(request, 'server/business_unit_delete_confirm.html', c)


@login_required
@required_level(ProfileLevel.global_admin)
def really_delete_business_unit(request, bu_id):
    business_unit = get_object_or_404(BusinessUnit, pk=int(bu_id))
    business_unit.delete()
    return redirect(index)


@login_required
@access_required(BusinessUnit)
def bu_dashboard(request, **kwargs):
    business_unit = kwargs['business_unit']
    machine_groups = business_unit.machinegroup_set.all()

    # Load in the default plugins if needed
    utils.load_default_plugins()
    plugins = sal.plugin.PluginManager().get_all_plugins()

    reports = utils.get_report_names(plugins)
    output = utils.get_plugin_placeholder_markup(
        plugins, group_type='business_unit', group_id=business_unit.id)

    context = {
        'user': request.user,
        'machine_groups': machine_groups,
        'business_unit': business_unit,
        'output': output,
        'reports': reports}
    return render(request, 'server/bu_dashboard.html', context)


@login_required
@required_level(ProfileLevel.global_admin)
def delete_machine_group(request, group_id):
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))

    machines = []
    # for machine_group in machine_groups:
    #     machines.append(machine_group.machine_set.all())

    machines = Machine.deployed_objects.filter(machine_group=machine_group)

    c = {'user': request.user, 'machine_group': machine_group, 'machines': machines}
    return render(request, 'server/machine_group_delete_confirm.html', c)


@login_required
@required_level(ProfileLevel.global_admin)
def really_delete_machine_group(request, group_id):
    machine_group = get_object_or_404(MachineGroup, pk=int(group_id))
    business_unit = machine_group.business_unit
    machine_group.delete()
    return redirect('bu_dashboard', business_unit.id)


@login_required
@access_required(MachineGroup)
def group_dashboard(request, **kwargs):
    machine_group = kwargs['instance']
    machines = machine_group.machine_set.filter(deployed=True)  # noqa: F841
    plugins = sal.plugin.PluginManager().get_all_plugins()
    output = utils.get_plugin_placeholder_markup(
        plugins, group_type='machine_group', group_id=machine_group.id)
    reports = utils.get_report_names(plugins)

    context = {
        'user': request.user,
        'machine_group': machine_group,
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

    if Plugin.objects.filter(name='Uptime'):
        try:
            plugin_script_submission = PluginScriptSubmission.objects.get(
                machine=machine, plugin='Uptime')
            uptime_seconds = PluginScriptRow.objects.get(
                submission=plugin_script_submission,
                pluginscript_name='UptimeSeconds').pluginscript_data
        except Exception:
            uptime_seconds = '0'

        uptime = utils.display_time(int(uptime_seconds))
    else:
        uptime = None

    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()

    output = utils.get_machine_detail_placeholder_markup(machine)

    # Process machine's managed items for display in the template.
    managed_items_queryset = ManagedItem.objects.filter(machine=machine)
    managed_items = defaultdict(dict)
    for item in managed_items_queryset:
        if item.data:
            try:
                data = json.loads(item.data)
            except json.decoder.JSONDecodeError:
                data = {}

        # Structure is a dict with keys for each source; each source
        # will then have as many sub types as ManagedItem.data "types".
        # The final structure is a list of ManagedItems.
        data_type = data.get('type')
        if data_type not in managed_items[item.management_source.name]:
            managed_items[item.management_source.name][data.get('type')] = []
        managed_items[item.management_source.name][data.get('type')].append(item)

    # Determine which tab to display first.
    # TODO: Do we just use the first, or configure for each OS / source?
    if machine.os_family == 'Darwin':
        initial_source = 'munki'
        active_table = 'ManagedInstalls'
    else:
        sources = sorted([s for s in managed_items])
        initial_source = sources[0] if sources else ''
        active_table = list(managed_items[initial_source].keys())[0] if initial_source else ''

    context = {
        'user': request.user,
        'machine_group': machine_group,
        'business_unit': business_unit,
        'report': report,
        'managed_items': dict(managed_items),
        'fact_sources': get_fact_sources(machine),
        'initial_source': initial_source,
        'active_table': active_table,
        'statuses': STATUSES,
        'machine': machine,
        'ip_address': ip_address,
        'uptime': uptime,
        'output': output}
    return render(request, 'server/machine_detail.html', context)


def get_fact_sources(machine):
    return (
        machine
        .facts
        .order_by('management_source__name')
        .values_list('management_source__name', flat=True)
        .distinct())


@login_required
@access_required(Machine)
def machine_detail_facts(request, machine_id, management_source, **kwargs):
    machine = kwargs['instance']
    table_data = []
    if machine.facts.count() != 0:
        facts = machine.facts.filter(management_source__name=management_source)
        if settings.EXCLUDED_FACTS:
            facts = facts.exclude(fact_name__in=settings.EXCLUDED_FACTS)
    else:
        facts = None

    if facts:
        for fact in facts:
            item = {}
            item['key'] = fact.fact_name
            item['value'] = fact.fact_data
            table_data.append(item)

    # table_data = list of dict(key, value)

    key_header = 'Fact'
    value_header = 'Data'
    title = f'{ management_source } Facts for { machine.hostname }'
    page_length = utils.get_setting('datatable_page_length')
    c = {
        'user': request.user,
        'machine': machine,
        'management_source': management_source,
        'fact_sources': get_fact_sources(machine),
        'table_data': table_data,
        'title': title,
        'key_header': key_header,
        'value_header': value_header,
        'page_length': page_length
    }
    return render(request, 'server/machine_detail_facts.html', c)


@login_required
@access_required(Machine)
def machine_detail_facter(request, machine_id, **kwargs):
    machine = kwargs['instance']
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
    page_length = utils.get_setting('datatable_page_length')
    c = {
        'user': request.user,
        'machine': machine,
        'table_data': table_data,
        'title': title,
        'key_header': key_header,
        'value_header': value_header,
        'page_length': page_length
    }
    return render(request, 'server/machine_detail_table.html', c)


@login_required
@access_required(Machine)
def machine_detail_conditions(request, machine_id, **kwargs):
    machine = kwargs['instance']
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
    page_length = utils.get_setting('datatable_page_length')
    c = {
        'user': request.user,
        'machine': machine,
        'table_data': table_data,
        'title': title,
        'key_header': key_header,
        'value_header': value_header,
        'page_length': page_length
    }
    return render(request, 'server/machine_detail_table.html', c)


@login_required
@required_level(ProfileLevel.global_admin, ProfileLevel.read_write)
@access_required(Machine)
def delete_machine(request, **kwargs):
    machine = kwargs['instance']
    machine_group_id = machine.machine_group.id
    machine.delete()
    return redirect('group_dashboard', machine_group_id)
