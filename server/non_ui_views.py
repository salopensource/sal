import hashlib
import itertools
import json
import re
from datetime import datetime, timedelta

import dateutil.parser
import pytz
import unicodecsv as csv

import django.utils.timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q, Count
from django.http import (HttpResponse, HttpResponseNotFound, JsonResponse, StreamingHttpResponse)
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inventory.models import Inventory
from sal.decorators import key_auth_required
from sal.plugin import (Widget, ReportPlugin, OldPluginAdapter, PluginManager,
                        DEPRECATED_PLUGIN_TYPES)
from server import text_utils
from server import utils
from server.models import (Machine, Condition, Fact, HistoricalFact, MachineGroup, UpdateHistory,
                           UpdateHistoryItem, InstalledUpdate, PendingAppleUpdate,
                           PluginScriptSubmission, PendingUpdate, Plugin, Report,
                           MachineDetailPlugin)

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = utils.is_postgres()
IGNORED_CSV_FIELDS = ('id', 'machine_group', 'report', 'activity', 'os_family')
UPDATE_META = {
    'ItemsToInstall':
        {'update_type': 'third_party', 'version_key': 'version_to_install',
            'status': 'pending'},
    'AppleUpdates':
        {'update_type': 'apple', 'version_key': 'version_to_install', 'status': 'pending'},
    'InstallResults': {'status': 'install'},
    'RemovalResults': {'status': 'removal'}}


@login_required
def tableajax(request, plugin_name, data, group_type='all', group_id=None):
    """Table ajax for dataTables"""
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

    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    queryset = plugin_object.get_queryset(
        request, group_type=group_type, group_id=group_id)
    machines, _ = plugin_object.filter_machines(queryset, data)

    if len(order_name) != 0:
        if order_direction == 'desc':
            order_string = "-%s" % order_name
        else:
            order_string = "%s" % order_name

    if len(search_value) != 0:
        searched_machines = machines.filter(
            Q(hostname__icontains=search_value) |
            Q(console_user__icontains=search_value) |
            Q(last_checkin__icontains=search_value)).order_by(order_string)
    else:
        searched_machines = machines.order_by(order_string)

    limited_machines = searched_machines[start:(start + length)]

    return_data = {}
    return_data['draw'] = int(draw)
    return_data['recordsTotal'] = machines.count()
    return_data['recordsFiltered'] = return_data['recordsTotal']

    return_data['data'] = []
    settings_time_zone = None
    try:
        settings_time_zone = pytz.timezone(settings.TIME_ZONE)
    except Exception:
        pass
    for machine in limited_machines:
        if machine.last_checkin:
            # formatted_date = pytz.utc.localize(machine.last_checkin)
            if settings_time_zone:
                formatted_date = machine.last_checkin.astimezone(
                    settings_time_zone).strftime("%Y-%m-%d %H:%M %Z")
            else:
                formatted_date = machine.last_checkin.strftime("%Y-%m-%d %H:%M")
        else:
            formatted_date = ""
        hostname_link = "<a href=\"%s\">%s</a>" % (
            reverse('machine_detail', args=[machine.id]), machine.hostname)

        list_data = [hostname_link, machine.console_user, formatted_date]
        return_data['data'].append(list_data)

    return JsonResponse(return_data)


@login_required
def plugin_load(request, plugin_name, group_type='all', group_id=None):
    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    return HttpResponse(
        plugin_object.widget_content(request, group_type=group_type, group_id=group_id))


def process_plugin(request, plugin_name, group_type='all', group_id=None):
    plugin = PluginManager().get_plugin_by_name(plugin_name)

    # Ensure that a plugin was instantiated before proceeding.
    if not plugin:
        raise Http404

    # Ensure the request is not for a disabled plugin.
    # TODO: This is to handle old-school plugins. It can be removed at
    # the next major version.
    if isinstance(plugin, OldPluginAdapter):
        model = DEPRECATED_PLUGIN_TYPES[plugin.get_plugin_type()]
    elif isinstance(plugin, Widget):
        model = Plugin
    elif isinstance(plugin, ReportPlugin):
        model = Report
    else:
        model = MachineDetailPlugin
        get_object_or_404(model, name=plugin_name)

    return plugin


class Echo(object):
    """Implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers):
    row = []
    for name, value in machine.get_fields():
        if name not in IGNORED_CSV_FIELDS:
            try:
                row.append(text_utils.safe_unicode(value))
            except Exception:
                row.append('')

    row.append(machine.machine_group.business_unit.name)
    row.append(machine.machine_group.name)
    return row


def stream_csv(header_row, machines, facter_headers, condition_headers, plugin_script_headers):
    """Helper function to inject headers"""
    if header_row:
        yield header_row
    for machine in machines:
        yield get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers)


@login_required
def export_csv(request, plugin_name, data, group_type='all', group_id=None):
    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    queryset = plugin_object.get_queryset(
        request, group_type=group_type, group_id=group_id)
    machines, title = plugin_object.filter_machines(queryset, data)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if not field.is_relation and field.name not in IGNORED_CSV_FIELDS:
            header_row.append(field.name)

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

    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title
    return response


@csrf_exempt
@key_auth_required
def preflight(request):
    """osquery plugins aren't a thing anymore.

    This is just to stop old clients from barfing.
    """
    output = {'queries': {}}
    return HttpResponse(json.dumps(output))


@csrf_exempt
@key_auth_required
def preflight_v2(request):
    """Find plugins that have embedded preflight scripts."""
    # Load in the default plugins if needed
    utils.load_default_plugins()
    manager = PluginManager()
    output = []
    # Old Sal scripts just do a GET; just send everything in that case.
    os_family = None if request.method != 'POST' else request.POST.get('os_family')

    enabled_reports = Report.objects.all()
    enabled_plugins = Plugin.objects.all()
    enabled_detail_plugins = MachineDetailPlugin.objects.all()
    for enabled_plugin in itertools.chain(enabled_reports, enabled_plugins, enabled_detail_plugins):
        plugin = manager.get_plugin_by_name(enabled_plugin.name)
        if os_family is None or os_family in plugin.get_supported_os_families():
            scripts = utils.get_plugin_scripts(plugin, hash_only=True)
            if scripts:
                output += scripts

    return HttpResponse(json.dumps(output))


@csrf_exempt
@key_auth_required
def preflight_v2_get_script(request, plugin_name, script_name):
    output = []
    plugin = PluginManager().get_plugin_by_name(plugin_name)
    if plugin:
        content = utils.get_plugin_scripts(plugin, script_name=script_name)
        if content:
            output += content

    return HttpResponse(json.dumps(output))


@csrf_exempt
@require_POST
@key_auth_required
def checkin(request):
    # TODO: Move these closer to where they're used.
    data = request.POST
    key = data.get('key')
    uuid = data.get('uuid')
    serial = data.get('serial')
    serial = serial.upper()
    broken_client = data.get('broken_client', False)

    # TODO: This can be a one liner
    # Take out some of the weird junk VMware puts in. Keep an eye out in case
    # Apple actually uses these:
    serial = serial.replace('/', '')
    serial = serial.replace('+', '')

    # TODO: This can be tightend up (except attribute error? or hasattr w/ternary)
    # Are we using Sal for some sort of inventory (like, I don't know, Puppet?)
    try:
        add_new_machines = settings.ADD_NEW_MACHINES
    except Exception:
        add_new_machines = True

    if add_new_machines:
        # TODO: get_or_create
        # look for serial number - if it doesn't exist, create one
        if serial:
            try:
                machine = Machine.objects.get(serial=serial)
            except Machine.DoesNotExist:
                machine = Machine(serial=serial)
    else:
        machine = get_object_or_404(Machine, serial=serial)

    # TODO: As per above ADD_NEW_MACHINES
    try:
        deployed_on_checkin = settings.DEPLOYED_ON_CHECKIN
    except Exception:
        deployed_on_checkin = True

    # TODO: Use `in`
    if key is None or key == 'None':
        # TODO: As per above settings rewrites
        try:
            key = settings.DEFAULT_MACHINE_GROUP_KEY
        except Exception:
            pass

    machine_group = get_object_or_404(MachineGroup, key=key)
    machine.machine_group = machine_group

    machine.last_checkin = django.utils.timezone.now()

    if bool(broken_client):
        machine.broken_client = True
        machine.save()
        return HttpResponse("Broken Client report submmitted for %s"
                            % data.get('serial'))
    else:
        # TODO: This defaults to false. Remove.
        machine.broken_client = False

    # TODO: Move to where it's needed.
    historical_days = utils.get_setting('historical_retention')

    # TODO: Compact all of this one-line attribute setting pieces.
    machine.hostname = data.get('name', '<NO NAME>')

    # TODO: This can be one or two lines.
    if 'username' in data:
        if data.get('username') != '_mbsetupuser':
            machine.console_user = data.get('username')

    # TODO: Rename some things so `report` is less generic.
    for key in ('bz2report', 'base64report', 'base64bz2report'):
        if key in data:
            machine.update_report(data[key], report_format=key)
            break

    # TODO: Compact with other one liners.
    if 'sal_version' in data:
        machine.sal_version = data.get('sal_version')

    # TODO: THis is where I stopped for the night y'all.

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

    # if gosal is the sender look for OSVers key
    if 'OSVers' in report_data['MachineInfo']:
        machine.operating_system = report_data['MachineInfo'].get(
            'OSVers')

    machine.hd_space = report_data.get('AvailableDiskSpace') or 0
    machine.hd_total = int(data.get('disk_size')) or 0

    if machine.hd_total == 0:
        machine.hd_percent = 0
    else:
        machine.hd_percent = int(
            round(
                ((float(
                    machine.hd_total) -
                    float(
                    machine.hd_space)) /
                    float(
                    machine.hd_total)) *
                100))
    machine.munki_version = report_data.get('ManagedInstallVersion') or 0
    hwinfo = {}
    # macOS System Profiler
    if 'SystemProfile' in report_data.get('MachineInfo', []):
        for profile in report_data['MachineInfo']['SystemProfile']:
            if profile['_dataType'] == 'SPHardwareDataType':
                hwinfo = profile._items[0]
                break
    if 'HardwareInfo' in report_data.get('MachineInfo', []):
        hwinfo = report_data['MachineInfo']['HardwareInfo']
    if 'Puppet' in report_data:
        puppet = report_data.get('Puppet')
        if 'time' in puppet:
            last_run_epoch = float(puppet['time']['last_run'])
            machine.last_puppet_run = datetime.fromtimestamp(last_run_epoch, tz=pytz.UTC)
        if 'events' in puppet:
            machine.puppet_errors = puppet['events']['failure']

    if hwinfo:
        # setup vars for hash keys we might get sent
        if 'MachineModel' in hwinfo:
            var_machine_model = 'MachineModel'
            var_cpu_type = 'CPUType'
            var_cpu_speed = 'CurrentProcessorSpeed'
            var_memory = 'PhysicalMemory'
        else:
            var_machine_model = 'machine_model'
            var_cpu_type = 'cpu_type'
            var_cpu_speed = 'current_processor_speed'
            var_memory = 'physical_memory'

        machine.machine_model = hwinfo.get(var_machine_model)
        machine.cpu_type = hwinfo.get(var_cpu_type)
        machine.cpu_speed = hwinfo.get(var_cpu_speed)
        machine.memory = hwinfo.get(var_memory)

        if hwinfo.get(var_memory)[-2:] == 'KB':
            machine.memory_kb = int(hwinfo.get(var_memory)[:-3])
        if hwinfo.get(var_memory)[-2:] == 'MB':
            memory_mb = float(hwinfo.get(var_memory)[:-3])
            machine.memory_kb = int(memory_mb * 1024)
        if hwinfo.get(var_memory)[-2:] == 'GB':
            memory_gb = float(hwinfo.get(var_memory)[:-3])
            machine.memory_kb = int(memory_gb * 1024 * 1024)
        if hwinfo.get(var_memory)[-2:] == 'TB':
            memory_tb = float(hwinfo.get(var_memory)[:-3])
            machine.memory_kb = int(memory_tb * 1024 * 1024 * 1024)

    if 'os_family' in report_data:
        machine.os_family = report_data['os_family']

    # support golang strict structure
    if 'OSFamily' in report_data:
        machine.os_family = report_data['OSFamily']

    if not machine.machine_model_friendly:
        try:
            machine.machine_model_friendly = utils.friendly_machine_model(machine)
        except Exception:
            machine.machine_model_friendly = machine.machine_model

    if deployed_on_checkin is True:
        machine.deployed = True

    machine.save()

    # If Plugin_Results are in the report, handle them
    try:
        datelimit = django.utils.timezone.now() - timedelta(days=historical_days)
        PluginScriptSubmission.objects.filter(recorded__lt=datelimit).delete()
    except Exception:
        pass

    if 'Plugin_Results' in report_data:
        utils.process_plugin_script(report_data.get('Plugin_Results'), machine)

    # Process Munki updates and removals.
    now = django.utils.timezone.now()
    items_to_create = []

    # We're only interested in what's currently pending...
    UpdateHistoryItem.objects.filter(update_history__machine=machine, status='pending').delete()

    for key, meta in UPDATE_META.items():
        for update in report_data.get(key, []):
            update_name = update.get('name')
            display_name = update.get('display_name', update_name)
            version = update.get(meta.get('version_key'), 'version').strip()
            if 'update_type' in meta:
                update_type = meta.get('update_type')
            else:
                update_type = 'apple' if update.get('apple_sus') else 'third_party'

            if 'status' in update and update['status'] != 0:
                status = 'error'
            else:
                status = meta['status']

            update_history, _ = UpdateHistory.objects.get_or_create(
                name=update_name, version=version, machine=machine, update_type=update_type)
            update_history_item = UpdateHistoryItem(
                update_history=update_history, status=status, recorded=now, uuid=uuid)

            if IS_POSTGRES:
                items_to_create.append(update_history_item)
            else:
                update_history_item.save()

    if IS_POSTGRES:
        UpdateHistoryItem.objects.bulk_create(items_to_create)

    # Remove any UpdateHistories that have no UpdateHistoryItems
    (UpdateHistory.objects
     .filter(machine=machine)
     .annotate(items=Count('updatehistoryitem'))
     .filter(items=0)
     .delete())

    # if Facter data is submitted, we need to first remove any existing facts for this machine
    if IS_POSTGRES:
        # If we are using postgres, we can just dump them all and do a bulk create
        if 'Facter' in report_data:
            facts = machine.facts.all()
            if facts.exists():
                facts._raw_delete(facts.db)
            try:
                datelimit = django.utils.timezone.now() - timedelta(days=historical_days)
                hist_to_delete = HistoricalFact.objects.filter(fact_recorded__lt=datelimit)
                if hist_to_delete.exists():
                    hist_to_delete._raw_delete(hist_to_delete.db)
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
                if skip:
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
                if not skip:
                    continue
                found = False
                for fact_name, fact_data in report_data['Facter'].iteritems():

                    if fact.fact_name == fact_name:
                        found = True
                        break
                if not found:
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
                if machine.os_family == 'Windows':
                    # We had a little trouble parsing out facts on Windows, clean up here
                    if fact_name.startswith('value=>'):
                        fact_name = fact_name.replace('value=>', '', 1)

                # does fact exist already?
                found = False
                skip = False
                if hasattr(settings, 'IGNORE_FACTS'):
                    for prefix in settings.IGNORE_FACTS:

                        if fact_name.startswith(prefix):
                            skip = True
                            break
                if skip:
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
                if not found:

                    fact = Fact(machine=machine, fact_data=fact_data, fact_name=fact_name)
                    fact.save()

                if fact_name in historical_facts:
                    fact = HistoricalFact(
                        machine=machine, fact_name=fact_name, fact_data=fact_data,
                        fact_recorded=datetime.now(tz=pytz.UTC))
                    fact.save()

    if IS_POSTGRES:
        if 'Conditions' in report_data:
            conditions_to_delete = machine.conditions.all()
            if conditions_to_delete.exists():
                conditions_to_delete._raw_delete(conditions_to_delete.db)
            conditions_to_be_created = []
            for condition_name, condition_data in report_data['Conditions'].iteritems():
                # Skip the conditions that come from facter
                if 'Facter' in report_data and condition_name.startswith('facter_'):
                    continue

                condition_data = text_utils.stringify(condition_data)
                conditions_to_be_created.append(
                    Condition(
                        machine=machine,
                        condition_name=condition_name,
                        condition_data=text_utils.safe_unicode(condition_data)
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
                if found is False:
                    condition.delete()

            conditions = machine.conditions.all()
            for condition_name, condition_data in report_data['Conditions'].iteritems():
                # Skip the conditions that come from facter
                if 'Facter' in report_data and condition_name.startswith('facter_'):
                    continue

                # if it's a list (more than one result),
                # we're going to conacetnate it into one comma separated string.
                condition_data = text_utils.stringify(condition_data)

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
                if found is False:
                    condition = Condition(machine=machine, condition_name=condition_name,
                                          condition_data=text_utils.safe_unicode(condition_data))
                    condition.save()

    utils.run_plugin_processing(machine, report_data)

    if utils.get_setting('send_data') in (None, True):
        # If setting is None, it hasn't been configured yet; assume True
        utils.send_report()

    return HttpResponse("Sal report submmitted for %s"
                        % data.get('name'))


# TODO: Remove after sal-scripts have reasonably been updated to not hit
# this endpoint.
@csrf_exempt
@key_auth_required
def install_log_hash(request, serial):
    sha256hash = hashlib.sha256('Update sal-scripts!').hexdigest()
    return HttpResponse(sha256hash)


# TODO: Remove after sal-scripts have reasonably been updated to not hit
# this endpoint.
@csrf_exempt
@key_auth_required
def install_log_submit(request):
    return HttpResponse("Update sal-scripts!")
