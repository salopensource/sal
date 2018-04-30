import hashlib
import itertools
import json
import plistlib
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
IGNORED_CSV_FIELDS = ('id', 'machine_group', 'report', 'os_family')
HISTORICAL_FACTS = utils.get_django_setting('HISTORICAL_FACTS', [])
IGNORE_PREFIXES = utils.get_django_setting('IGNORE_FACTS', [])
# TODO: This is temporary, and will be corrected: ItemsToRemove were not originally added here.
UPDATE_META = {
    'ItemsToInstall':
        {'update_type': 'third_party', 'version_key': 'version_to_install',
         'status': 'pending'},
    'ItemsToRemove':
        {'update_type': 'third_party', 'version_key': 'installed_version',
         'status': 'pending'},
    'AppleUpdates':
        {'update_type': 'apple', 'version_key': 'version_to_install', 'status': 'pending'},
    'InstallResults': {'status': 'install'},
    'RemovalResults': {'status': 'removal'}}
MACHINE_KEYS = {
    'machine_model': {'old': 'MachineModel', 'new': 'machine_model'},
    'cpu_type': {'old': 'CPUType', 'new': 'cpu_type'},
    'cpu_speed': {'old': 'CurrentProcessorSpeed', 'new': 'current_processor_speed'},
    'memory': {'old': 'PhysicalMemory', 'new': 'physical_memory'}}
MEMORY_EXPONENTS = {'KB': 0, 'MB': 1, 'GB': 2, 'TB': 3}
# Build a translation table for serial numbers, to remove garbage
# VMware puts in.
SERIAL_TRANSLATE = {ord(c): None for c in '+/'}


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
        if not plugin:
            continue
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
    data = request.POST

    # Take out some of the weird junk VMware puts in. Keep an eye out in case
    # Apple actually uses these:
    serial = data.get('serial', '').upper().translate(SERIAL_TRANSLATE)
    # Are we using Sal for some sort of inventory (like, I don't know, Puppet?)
    if utils.get_django_setting('ADD_NEW_MACHINES', True):
        if serial:
            try:
                machine = Machine.objects.get(serial=serial)
            except Machine.DoesNotExist:
                machine = Machine(serial=serial)
    else:
        machine = get_object_or_404(Machine, serial=serial)

    machine_group_key = data.get('key')
    if machine_group_key in (None,'None'):
        machine_group_key = utils.get_django_setting('DEFAULT_MACHINE_GROUP_KEY')
    machine.machine_group = get_object_or_404(MachineGroup, key=machine_group_key)

    machine.last_checkin = django.utils.timezone.now()
    machine.hostname = data.get('name', '<NO NAME>')
    machine.sal_version = data.get('sal_version')
    machine.console_user = data.get('username') if data.get('username') != '_mbsetupuser' else None

    if utils.get_django_setting('DEPLOYED_ON_CHECKIN', True):
        machine.deployed = True

    if bool(data.get('broken_client', False)):
        machine.broken_client = True
        machine.save()
        return HttpResponse("Broken Client report submmitted for %s" % data.get('serial'))

    report = None
    report_format = None
    # Find the report in the submitted data. It could be encoded
    # and/or compressed with base64 and bz2.
    for key in ('bz2report', 'base64report', 'base64bz2report'):
        if key in data:
            encoded_report = data[key]
            report = text_utils.decode_to_string(encoded_report, compression=key)
            # TODO: Pending removal
            report_format = key.replace('report', '')
            break

    machine.report = report
    machine.report_format = report_format

    if not report:
        machine.activity = False
        machine.errors = machine.warnings = 0
        return

    report_data = plistlib.readPlistFromString(report)

    machine.activity = any(report_data.get(s) for s in UPDATE_META.keys())

    # Check errors and warnings.
    machine.errors = len(report_data.get("Errors", []))
    machine.warnings = len(report_data.get("Warnings", []))

    machine.puppet_version = report_data.get('Puppet_Version')
    machine.manifest = report_data.get('ManifestName')
    machine.munki_version = report_data.get('ManagedInstallVersion')

    puppet = report_data.get('Puppet', {})
    if 'time' in puppet:
        last_run_epoch = float(puppet['time']['last_run'])
        machine.last_puppet_run = datetime.fromtimestamp(last_run_epoch, tz=pytz.UTC)
    if 'events' in puppet:
        machine.puppet_errors = puppet['events']['failure']

    # Handle gosal submissions slightly differently from others.
    machine.os_family = (
        report_data['OSFamily'] if 'OSFamily' in report_data else report_data.get('os_family'))

    machine_info = report_data.get('MachineInfo', {})
    if 'os_vers' in machine_info:
        machine.operating_system = machine_info['os_vers']
        # macOS major OS updates don't have a minor version, so add one.
        if len(machine.operating_system) <= 4:
            machine.operating_system = machine.operating_system + '.0'
    else:
        # Handle gosal and missing os_vers cases.
        machine.operating_system = machine_info.get('OSVers')

    # TODO: These should be a number type.
    # TODO: Cleanup all of the casting to str if we make a number.
    machine.hd_space = report_data.get('AvailableDiskSpace', '0')
    machine.hd_total = data.get('disk_size', '0')
    space = float(machine.hd_space)
    total = float(machine.hd_total)
    if machine.hd_total == 0:
        machine.hd_percent = '0'
    else:
        machine.hd_percent = str(int((total - space) / total * 100))

    # Get macOS System Profiler hardware info.
    # Older versions use `HardwareInfo` key, so start there.
    hwinfo = machine_info.get('HardwareInfo', {})
    if not hwinfo:
        for profile in machine_info.get('SystemProfile', []):
            if profile['_dataType'] == 'SPHardwareDataType':
                hwinfo = profile._items[0]
                break

    if hwinfo:
        key_style = 'old' if 'MachineModel' in hwinfo else 'new'
        machine.machine_model = hwinfo.get(MACHINE_KEYS['machine_model'][key_style])
        machine.cpu_type = hwinfo.get(MACHINE_KEYS['cpu_type'][key_style])
        machine.cpu_speed = hwinfo.get(MACHINE_KEYS['cpu_speed'][key_style])
        machine.memory = hwinfo.get(MACHINE_KEYS['memory'][key_style])
        machine.memory_kb = int(machine.memory[:-3]) ** MEMORY_EXPONENTS[machine.memory[-2:]]

    if not machine.machine_model_friendly:
        try:
            machine.machine_model_friendly = utils.friendly_machine_model(machine)
        except Exception:
            machine.machine_model_friendly = machine.machine_model

    machine.save()

    historical_days = utils.get_setting('historical_retention')
    datelimit = django.utils.timezone.now() - timedelta(days=historical_days)

    # Process plugin scripts.
    # Clear out too-old plugin script submissions first.
    PluginScriptSubmission.objects.filter(recorded__lt=datelimit).delete()
    utils.process_plugin_script(report_data.get('Plugin_Results', []), machine)

    # Process Munki updates and removals.
    now = django.utils.timezone.now()
    items_to_create = []

    # We're only interested in what's currently pending, use raw delete
    # save some cycles.
    histories_to_delete = UpdateHistoryItem.objects.filter(
        update_history__machine=machine, status='pending')
    if histories_to_delete.exists():
        histories_to_delete._raw_delete(histories_to_delete.db)

    uuid = data.get('uuid')
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

            items_to_create.append(update_history_item)

    if IS_POSTGRES:
        UpdateHistoryItem.objects.bulk_create(items_to_create)
    else:
        for update_history_item in items_to_create:
            update_history_item.save()

    # Remove any UpdateHistories that have no UpdateHistoryItems
    (UpdateHistory.objects
     .filter(machine=machine)
     .annotate(items=Count('updatehistoryitem'))
     .filter(items=0)
     .delete())

    facts_to_be_created = []
    historical_facts_to_be_created = []

    # TODO: May need to come through and do get_or_create on machine, name, updating data, and
    # deleting now missing facts and conditions for non-postgres.
    # if Facter data is submitted, we need to first remove any existing facts for this machine
    facts = machine.facts.all()
    if facts.exists():
        facts._raw_delete(facts.db)
    hist_to_delete = HistoricalFact.objects.filter(fact_recorded__lt=datelimit)
    if hist_to_delete.exists():
        hist_to_delete._raw_delete(hist_to_delete.db)

    facts_to_be_created = []
    historical_facts_to_be_created = []
    for fact_name, fact_data in report_data.get('Facter', {}).items():
        if any(fact_name.startswith(p) for p in IGNORE_PREFIXES):
            continue

        facts_to_be_created.append(
            Fact(machine=machine, fact_data=fact_data, fact_name=fact_name))

        if fact_name in HISTORICAL_FACTS:
            historical_facts_to_be_created.append(
                HistoricalFact(machine=machine, fact_data=fact_data, fact_name=fact_name))

    if facts_to_be_created:
        if IS_POSTGRES:
            Fact.objects.bulk_create(facts_to_be_created)
        else:
            for fact in facts_to_be_created:
                fact.save()
    if historical_facts_to_be_created:
        if IS_POSTGRES:
            HistoricalFact.objects.bulk_create(historical_facts_to_be_created)
        else:
            for fact in historical_facts_to_be_created:
                fact.save()

    conditions_to_delete = machine.conditions.all()
    if conditions_to_delete.exists():
        conditions_to_delete._raw_delete(conditions_to_delete.db)
    conditions_to_be_created = []
    for condition_name, condition_data in report_data.get('Conditions', {}).items():
        # Skip the conditions that come from facter
        if 'Facter' in report_data and condition_name.startswith('facter_'):
            continue

        condition_data = text_utils.safe_unicode(text_utils.stringify(condition_data))
        condition = Condition(
            machine=machine, condition_name=condition_name, condition_data=condition_data)
        conditions_to_be_created.append(condition)

    if conditions_to_be_created:
        if IS_POSTGRES:
            Condition.objects.bulk_create(conditions_to_be_created)
        else:
            for condition in conditions_to_be_created:
                condition.save()

    utils.run_plugin_processing(machine, report_data)

    if utils.get_setting('send_data') in (None, True):
        # If setting is None, it hasn't been configured yet; assume True
        utils.send_report()

    return HttpResponse("Sal report submmitted for %s" % data.get('name'))


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
