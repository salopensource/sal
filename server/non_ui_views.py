import hashlib
import itertools
import json
import logging
import plistlib
from collections import defaultdict
from datetime import datetime, timedelta

import dateutil.parser
import pytz

import django.utils.timezone
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import (
    HttpResponse, JsonResponse, HttpResponseServerError, Http404, HttpResponseBadRequest)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import server.utils
import utils.csv
from sal.decorators import key_auth_required
from sal.plugin import (Widget, ReportPlugin, OldPluginAdapter, PluginManager,
                        DEPRECATED_PLUGIN_TYPES)
from server.models import (Machine, Condition, Fact, HistoricalFact, MachineGroup, UpdateHistory,
                           UpdateHistoryItem, InstalledUpdate, PendingAppleUpdate,
                           PluginScriptSubmission, Plugin, Report, MachineDetailPlugin,
                           ManagementSource, ManagedItem)
from utils import text_utils

if settings.DEBUG:
    logging.basicConfig(level=logging.INFO)


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = server.utils.is_postgres()
HISTORICAL_FACTS = server.utils.get_django_setting('HISTORICAL_FACTS', [])
IGNORED_CSV_FIELDS = ('id', 'machine_group', 'report', 'os_family')
IGNORE_PREFIXES = server.utils.get_django_setting('IGNORE_FACTS', [])
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
    get_data = json.loads(get_data)
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
    machines = machines.values('id', 'hostname', 'console_user', 'last_checkin')

    if len(order_name) != 0:
        if order_direction == 'desc':
            order_string = "-%s" % order_name
        else:
            order_string = "%s" % order_name

    if len(search_value) != 0:
        hostname_q = Q(hostname__icontains=search_value)
        user_q = Q(console_user__icontains=search_value)
        checkin_q = Q(last_checkin__icontains=search_value)
        searched_machines = machines.filter(hostname_q | user_q | checkin_q).order_by(order_string)
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
        if machine['last_checkin']:
            # formatted_date = pytz.utc.localize(machine.last_checkin)
            if settings_time_zone:
                formatted_date = machine['last_checkin'].astimezone(
                    settings_time_zone).strftime("%Y-%m-%d %H:%M %Z")
            else:
                formatted_date = machine['last_checkin'].strftime("%Y-%m-%d %H:%M")
        else:
            formatted_date = ""
        hostname_link = "<a href=\"%s\">%s</a>" % (
            reverse('machine_detail', args=[machine['id']]), machine['hostname'])

        list_data = [hostname_link, machine['console_user'], formatted_date]
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


@login_required
def export_csv(request, plugin_name, data, group_type='all', group_id=None):
    plugin_object = process_plugin(request, plugin_name, group_type, group_id)
    queryset = plugin_object.get_queryset(
        request, group_type=group_type, group_id=group_id)
    machines, title = plugin_object.filter_machines(queryset, data)

    return utils.csv.get_csv_response(machines, utils.csv.machine_fields(), title)


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
    server.utils.load_default_plugins()
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
            scripts = server.utils.get_plugin_scripts(plugin, hash_only=True)
            if scripts:
                output += scripts

    return HttpResponse(json.dumps(output))


@csrf_exempt
@key_auth_required
def preflight_v2_get_script(request, plugin_name, script_name):
    output = []
    plugin = PluginManager().get_plugin_by_name(plugin_name)
    if plugin:
        content = server.utils.get_plugin_scripts(plugin, script_name=script_name)
        if content:
            output += content

    return HttpResponse(json.dumps(output))


@csrf_exempt
@require_POST
@key_auth_required
def checkin(request):
    if request.content_type != 'application/json':
        return HttpResponseBadRequest('Checkin must be content-type "application/json"!')
    # Ensure we have the bare minimum data before continuing.
    try:
        submission = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Checkin has invalid JSON!')
    if not isinstance(submission, dict) or 'machine' not in submission:
        return HttpResponseBadRequest('Checkin JSON is missing required key "machine"!')

    # Process machine submission information.
    machine_submission = submission['machine']
    serial = machine_submission.get('serial')
    if not serial:
        return HttpResponseBadRequest('Checkin JSON is missing required "machine" key "serial"!')

    machine = process_checkin_serial(submission['machine']['serial'])
    machine.hostname = machine_submission.get('hostname', '<NO NAME>')
    # TODO: Do we need to ignore "_mbsetupuser" still?
    machine.console_user = machine_submission.get('console_user')
    machine.os_family = machine_submission.get('os_family', 'Darwin')
    machine.operating_system = machine_submission.get('operating_system')
    machine.hd_space = machine_submission.get('hd_space')
    machine.hd_total = machine_submission.get('hd_total')
    machine.hd_percent = machine_submission.get('hd_percent')
    machine.machine_model = machine_submission.get('machine_model')
    machine.machine_model_friendly = machine_submission.get('machine_model_friendly')
    machine.cpu_type = machine_submission.get('cpu_type')
    machine.cpu_speed = machine_submission.get('cpu_speed')
    machine.memory = machine_submission.get('memory')
    machine.memory_kb = machine_submission.get('memory_kb', 0)

    # Process Sal checkin information.
    sal_submission = submission.get('sal', {})
    machine.machine_group = get_checkin_machine_group(sal_submission.get('key'))
    machine.sal_version = sal_submission.get('sal_version')
    machine.last_checkin = django.utils.timezone.now()

    if server.utils.get_django_setting('DEPLOYED_ON_CHECKIN', True):
        machine.deployed = True

    machine.save()

    # Cast to bool just in case.
    if bool(sal_submission.get('broken_client', False)):
        machine.broken_client = True
        machine.save()
        return HttpResponse("Broken Client report submmitted for %s" % serial)

    # Clear out existing Facts and start from scratch.
    facts = machine.facts.all()
    if facts.exists():
        facts._raw_delete(facts.db)

    # Clear out existing ManagedItems and start from scratch.
    managed_items = machine.manageditem_set.all()
    if managed_items.exists():
        managed_items._raw_delete(managed_items.db)

    object_queue = {
        'facts': [],
        'historical_facts': [],
        'managed_items': []}

    # TODO: This can come out when we do function swapping.
    core_modules = ('machine', 'sal')
    for management_source_name, management_data in submission.items():
        if management_source_name in core_modules:
            continue

        management_source, _ = ManagementSource.objects.get_or_create(name=management_source_name)
        object_queue = process_management_submission(
            management_source, management_data, machine, object_queue)

    create_objects(object_queue)

    server.utils.process_plugin_script(submission.get('plugin_results', []), machine)
    server.utils.run_plugin_processing(machine, submission)

    if server.utils.get_setting('send_data') in (None, True):
        # If setting is None, it hasn't been configured yet; assume True
        server.utils.send_report()

    msg = f"Sal report submmitted for {machine.serial}"
    logging.debug(msg)
    return HttpResponse(msg)


def process_management_submission(management_source, management_data, machine, object_queue):
    """Process a single management source's data

    This function first optionally calls any additional processors for
    the management source in question (Munki for example).

    Then it processes Facts.
    Then ManagedItems.
    """
    def default_func(management_data, machine):
        return

    # Add custom processor funcs to this dictionary.
    # The key should be the same name used in the submission for ManagementSource.
    # The func's signature must be f(management_data: dict, machine: Machine)
    processing_funcs = {'munki': process_munki_extra_keys}

    processing_func = processing_funcs.get(management_source.name, default_func)
    processing_func(management_data, machine)

    object_queue = process_facts(management_source, management_data, machine, object_queue)
    object_queue = process_managed_items(management_source, management_data, machine, object_queue)

    return object_queue


def process_facts(management_source, management_data, machine, object_queue):
    now = django.utils.timezone.now()
    for fact_name, fact_data in management_data.get('facts', {}).items():
        # TODO: Figure out how we're doing this in the process facts code.
        if any(fact_name.startswith(p) for p in IGNORE_PREFIXES):
            continue

        object_queue['facts'].append(
            Fact(machine=machine, fact_data=fact_data, fact_name=fact_name,
                    management_source=management_source))

        if fact_name in HISTORICAL_FACTS:
            object_queue['historical_facts'].append(
                HistoricalFact(
                    machine=machine, fact_data=fact_data, fact_name=fact_name,
                    management_source=management_source, fact_recorded=now))

    return object_queue


def process_managed_items(management_source, management_data, machine, object_queue):
    now = django.utils.timezone.now()
    for name, managed_item in management_data.get('managed_items', {}).items():
        submitted_date = managed_item.get('date_managed')
        date_managed = dateutil.parser.parse(submitted_date) if submitted_date else now
        status = managed_item.get('status', 'UNKNOWN')
        data = managed_item.get('data')
        dumped_data = json.dumps(data) if data else None
        object_queue['managed_items'].append(
            ManagedItem(
                name=name, machine=machine, management_source=management_source,
                date_managed=date_managed, status=status, data=dumped_data))

    return object_queue


def process_munki_extra_keys(management_data, machine):
    machine.munki_version = management_data.get('munki_version')
    machine.manifest = management_data.get('manifest')
    machine.save()
    process_update_history(management_data.get('update_history', []), machine)


def process_update_history(update_histories, machine):
    """Process Munki updates and removals."""
    # Delete all of these every run, as its faster than comparing
    # between the client/server and removing the difference.
    to_delete = machine.pending_apple_updates.all()
    if to_delete.exists():
        to_delete._raw_delete(to_delete.db)

    # Accumulate items to create, so we can do `bulk_create` on
    # supported databases.
    items_to_create = defaultdict(list)

    for update in update_histories:
        update_history, _ = UpdateHistory.objects.get_or_create(
            machine=machine, update_type=update['update_type'], name=update['name'],
            version=update['version'])

        # Only create a history item if there are none or
        # if the last one is not the same status.
        items_set = update_history.updatehistoryitem_set.order_by('recorded')
        status = update['status']
        recorded = update['date']
        if not items_set.exists() or needs_history_item_creation(items_set, status, recorded):
            items_to_create[UpdateHistoryItem].append(
                UpdateHistoryItem(update_history=update_history, status=status, recorded=recorded))

        if status == 'pending' and update['update_type'] == 'apple':
            pending_apple_item = PendingAppleUpdate(
                machine=machine, update=update['name'], update_version=update['version'],
                display_name=update.get('display_name'))
            items_to_create[PendingAppleUpdate].append(pending_apple_item)

    # Bulk create all of the objects we've built up.
    for model, updates_to_save in items_to_create.items():
        if IS_POSTGRES:
            model.objects.bulk_create(updates_to_save)
        else:
            for item in updates_to_save:
                item.save()


def create_objects(object_queue):
    """Bulk create Fact, HistoricalFact, and ManagedItem objects."""
    models = {'facts': Fact, 'historical_facts': HistoricalFact, 'managed_items': ManagedItem}

    for name, objects in object_queue.items():
        _bulk_create_or_iterate_save(objects, models[name])


def _bulk_create_or_iterate_save(objects, model):
    if objects and IS_POSTGRES:
        model.objects.bulk_create(objects)
    else:
        for item in objects:
            item.save()


def process_checkin_serial(serial):
    # Take out some of the weird junk VMware puts in. Keep an eye out in case
    # Apple actually uses these:
    serial = serial.upper().translate(SERIAL_TRANSLATE)

    # TODO: Remove this check once checkin_v2 is removed, as checkin_v3 handles this.
    # A serial number is required.
    if not serial:
        raise Http404

    # Are we using Sal for some sort of inventory (like, I don't know, Puppet?)
    if server.utils.get_django_setting('ADD_NEW_MACHINES', True):
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            machine = Machine(serial=serial)
    else:
        machine = get_object_or_404(Machine, serial=serial)
    return machine


def get_checkin_machine_group(key):
    if key in (None, 'None'):
        key = server.utils.get_django_setting('DEFAULT_MACHINE_GROUP_KEY')
    return get_object_or_404(MachineGroup, key=key)


def needs_history_item_creation(items_set, status, recorded):
    return items_set.last().status != status and items_set.last().recorded < recorded
