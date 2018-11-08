import hashlib
import itertools
import json
import logging
import os
import pathlib
import plistlib
import time
import xml.etree.ElementTree as ET
from distutils.version import LooseVersion
from itertools import chain

import requests

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404

from sal.decorators import is_global_admin
from sal.plugin import (BasePlugin, Widget, OldPluginAdapter, PluginManager, DetailPlugin,
                        ReportPlugin, DEPRECATED_PLUGIN_TYPES)
from server.models import *
from server.text_utils import safe_text


PLUGIN_ORDER = [
    'Activity', 'Status', 'OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory', 'DiskSpace',
    'PendingAppleUpdates', 'Pending3rdPartyUpdates', 'Encryption', 'Gatekeeper', 'Sip',
    'XprotectVersion']
PLUGIN_MODELS = {'machines': (Plugin, Widget), 'report': (Report, ReportPlugin),
                 'machine_detail': (MachineDetailPlugin, DetailPlugin)}
TRUTHY = {'TRUE', 'YES'}
FALSY = {'FALSE', 'NO'}
STRINGY_BOOLS = TRUTHY.union(FALSY)
TWENTY_FOUR_HOURS = 86400
EXCLUDED_SCRIPT_TYPES = ('.pyc',)


def db_table_exists(table_name):
    return table_name in connection.introspection.table_names()


def get_instance_and_groups(group_type, group_id):
    if group_type == 'all':
        return

    model = GROUP_NAMES[group_type]

    try:
        instance = get_object_or_404(model, pk=group_id)
    except ValueError:
        # Sal allows machine serials instead of machine ID in URLs.
        # Handle that special case.
        if model is Machine:
            instance = get_object_or_404(model, serial=group_id)

    result = {'instance': instance, 'model': model}

    if isinstance(instance, MachineGroup):
        result['business_unit'] = instance.business_unit
    elif isinstance(instance, Machine):
        result['business_unit'] = instance.machine_group.business_unit
    else:
        result['business_unit'] = instance

    return result


def get_server_version():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist'), 'rb') as handle:
        version = plistlib.load(handle)
    return version['version']


def get_current_release_version_number():
    """Get the currently available Sal version.

    Only checks once per 24 hours.

    Returns:
        (str) Version number if it could be retrieved, otherwise None.
    """
    last_version_check = get_setting('last_version_check_date', 0)
    current_time = time.time()
    current_version = None

    if last_version_check < (current_time - TWENTY_FOUR_HOURS):
        try:
            response = requests.get('https://version.salopensource.com')
            if response.status_code == 200:
                current_version = response.text
        except requests.exceptions.RequestException:
            pass

        if current_version:
            set_setting('last_version_check_date', int(current_time))
            set_setting('current_version', current_version)
    else:
        current_version = get_setting('current_version')

    return current_version


def get_install_type():
    if os.path.exists('/home/docker'):
        return 'docker'
    else:
        return 'bare'


def send_report():
    """Send report data if last report was sent over 24 hours ago."""
    last_sent = get_setting('last_sent_data', 0)

    current_time = time.time()

    if last_sent < (current_time - TWENTY_FOUR_HOURS):
        output = {}

        # get total number of machines
        output['machines'] = Machine.objects.count()

        # get list of plugins
        output['plugins'] = [p.name for p in chain(Plugin.objects.all(), Report.objects.all())]

        # get install type
        output['install_type'] = get_install_type()

        # get database type
        output['database'] = settings.DATABASES['default']['ENGINE']

        # version
        current_dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist')
        with open(path, 'rb') as handle:
            version = plistlib.load(handle)
        output['version'] = version['version']
        # plist encode output
        post_data = plistlib.dumps(output)
        response = requests.post('https://version.salopensource.com', data={"data": post_data})
        set_setting('last_sent_data', int(current_time))
        print(response.status_code)
        if response.status_code == 200:
            return response.text
        else:
            return None


def check_version():
    """Compare running version to available version and return info.

    This function honors the `next_notify_date` = 'never' setting, and only
    returns data if a notification is due to be delivered.

    Returns:
        dict:
            'new_version_available': (bool)
            'new_version': (str) Version number of available update.
            'current_version': (str) Version of running server.
    """
    # TODO: This is just to keep the values the same from existing code.
    result = {'new_version_available': False, 'new_version': False, 'server_version': False}

    server_version = get_server_version()
    current_release_version = get_current_release_version_number() or '0.0.0'

    # Only do something if running version is out of date.
    if LooseVersion(current_release_version) > LooseVersion(server_version):
        # Determine whether to notify, or just not bother.
        next_notify_date = get_setting('next_notify_date', 0)
        if next_notify_date == 'never':
            last_notified_version = get_setting('last_notified_version')
            if last_notified_version != current_release_version:
                set_setting('last_notified_version', current_release_version)
                set_setting('next_notify_date', '')

        current_time = time.time()
        if current_time > next_notify_date:
            result['new_version_available'] = True
            result['server_version'] = server_version
            result['current_release_version'] = current_release_version

    return result


def is_postgres():
    postgres_backend = 'django.db.backends.postgresql_psycopg2'
    db_setting = settings.DATABASES['default']['ENGINE']
    return db_setting == postgres_backend


def friendly_machine_model(machine):
    # See if the machine's model already has one (and only one) friendly name
    output = None
    if machine.machine_model_friendly and machine.machine_model_friendly != '':
        output = machine.machine_model_friendly

    if not output and not machine.serial.startswith('VM') and machine.os_family == 'Darwin':
        if len(machine.serial) > 11:
            serial_snippet = machine.serial[-4:]
        else:
            # older models product code is the last three characters of the serial
            serial_snippet = machine.serial[-3:]
        payload = {'cc': serial_snippet}
        try:
            friendly_cache_item = FriendlyNameCache.objects.get(serial_stub=serial_snippet)
            print(f'cache item is: {friendly_cache_item.friendly_name}')
            output = friendly_cache_item.friendly_name
        except FriendlyNameCache.DoesNotExist:
            output = None
            try:
                r = requests.get('http://support-sp.apple.com/sp/product', params=payload)
            except requests.exceptions.RequestException as e:
                print(machine.serial)
                print(e)

            try:
                output = ET.fromstring(r.text).find('configCode').text

                new_cache_item = FriendlyNameCache(
                    serial_stub=serial_snippet,
                    friendly_name=output
                )
                new_cache_item.save()
            except Exception as e:
                print(f'Did not receive a model name for {machine.serial}, '
                      f'{machine.machine_model}. Error: {e}')

    return output


def display_time(seconds, granularity=2):
    result = []
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),    # 60 * 60 * 24
        ('hours', 3600),    # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def get_setting(name, default=None):
    """Get a SalSetting from the database.

    If a setting is not in the database, and a default has been provided
    in 'sal/default_sal_settings.json', create it with that value.
    If no setting exists, and it's not in the defaults file, return
    default argument (default of `None`).

    Args:
        name (str): Name of SalSetting to retrieve.
        default (str, bool, float, int, None): Default value to return
            if setting has no value, the settings file has no configured
            defaults. Defaults to `None`.

    Returns:
        None: Value is an empty string or if the setting is absent from
            the database and has no default setting.
        int: Value is all digits with no decimal place.
        float: Value can be cast to a float.
        bool: If value is (any case) True, False, Yes, No.
        str: Anything else.

    """

    # Make sure migrations have run, otherwise return default
    if not db_table_exists('server_salsetting'):
        default_settings = get_defaults()
        for item in default_settings:
            if item['name'] == name:
                default = item['value']
                break
        return default

    try:
        setting = SalSetting.objects.get(name=name)
    except SalSetting.DoesNotExist:
        # Let's just refresh all of the missing defaults.
        add_default_sal_settings()
        # And try one more time.
        try:
            setting = SalSetting.objects.get(name=name)
        except SalSetting.DoesNotExist:
            # Otherwise, fall back to the default argument.
            return default

    # Cast values to python datatypes.
    value = setting.value.strip()
    if not value:
        return None if default is None else default
    elif value.isdigit():
        return int(value)
    elif is_float(value):
        return float(value)
    elif value.upper() in STRINGY_BOOLS:
        return True if value.upper() in TRUTHY else False
    else:
        return value


def add_default_sal_settings():
    """Add in missing default settings to database."""
    default_sal_settings = get_defaults()
    for setting in default_sal_settings:
        _, created = SalSetting.objects.get_or_create(
            name=setting['name'], defaults={'value': setting['value']})


def get_defaults():
    """Get the default settings from our defaults file."""
    # The file is stored in the project root /sal folder.
    default_sal_settings_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../sal", 'default_sal_settings.json')
    with open(default_sal_settings_path) as handle:
        default_sal_settings = json.load(handle)

    return default_sal_settings


def set_setting(name, value):
    """Set SalSetting with `name` to `value`.

    Args:
        name (str): Name of SalSetting to set.
        value (str or with __str__ method): Value to set. Must be
            castable to str.

    Returns:
        False if setting was not set (value conversion failed) or True
        if setting was successfully set.
    """
    try:
        value = str(value)
    except ValueError:
        return False

    obj, created = SalSetting.objects.get_or_create(name=name, defaults={'value': value})
    if not created:
        obj.value = value
        obj.save()
    return True


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def get_django_setting(name, default=None):
    """Get a setting from the Django.conf.settings object

    In Sal, that's anything in the system_settings or settings files.
    """
    return getattr(settings, name, default)


# Plugin utilities

def process_plugin_script(results, machine):
    rows_to_create = []

    results = get_newest_plugin_results(results)

    for plugin in results:
        plugin_name = plugin['plugin']
        historical = plugin.get('historical', False)
        if not historical:
            PluginScriptSubmission.objects.filter(
                machine=machine, plugin=safe_text(plugin_name)).delete()

        submission = PluginScriptSubmission.objects.create(
            machine=machine, plugin=safe_text(plugin_name), historical=historical)
        data = plugin.get('data')
        # Ill-formed plugin data will throw an exception here.
        if not isinstance(data, dict):
            return
        for key, value in data.items():
            plugin_row = PluginScriptRow(
                submission=submission,
                pluginscript_name=safe_text(key),
                pluginscript_data=safe_text(value),
                submission_and_script_name=(safe_text('{}: {}'.format(plugin_name, key))))
            if is_postgres():
                rows_to_create.append(plugin_row)
            else:
                plugin_row.save()

    if is_postgres() and rows_to_create:
        PluginScriptRow.objects.bulk_create(rows_to_create)


def get_newest_plugin_results(results):
    """Get the newest, correct results from plugin scripts.

    If the sal scripts fail to complete the plugin process, duplicate
    entries can be introduced into the results. Filter out all but the
    newest result for each plugin.
    Drop any results that don't have the required keys.
    """
    results = [result for result in results if is_valid_plugin_result(result)]

    # Since the last write to each dictionary key in this comprehension is
    # also the newest, (the sal_postflight appends results to the end), we can
    # then use just the `values()` method to get back a list of plugin results
    # dicts.
    return {result['plugin']: result for result in results}.values()


def is_valid_plugin_result(result):
    return not any(key not in result for key in ('plugin', 'data'))


def get_plugin_scripts(plugin, hash_only=False, script_name=None):
    """Get script files from plugins 'scripts' dir.

    Also, can retrieve a single script by name. Return value is always
    a list!

    Args:
        plugin (sal.plugin.BasePlugin): Plugin returned from a
            PluginManager.
        hash_only (bool): Return just the hash of the scripts or the
            entire script. Optional, defaults to False.
        script_name (str): Name of script to retrieve. Optional,
            defaults to None.

    Returns:
        List of dicts with key/value pairs of:
            plugin (str): Name of plugin.
            filename (str): Path to plugin.
            hash (str): SHA256 hash of script contents (hash_only).
            content (str): Content of script (NOT hash_only).
    """
    results = []
    plugin_path = pathlib.Path(plugin.path) / 'scripts'
    server_path = (pathlib.Path(plugin.path).parent / 'scripts').absolute()
    if plugin_path.exists():
        scripts_dir = plugin_path
    elif server_path.exists():
        scripts_dir = server_path
    else:
        return results

    if script_name:
        dir_contents = [pathlib.Path(script_name)]
    else:
        dir_contents = (p for p in scripts_dir.iterdir() if p.suffix not in EXCLUDED_SCRIPT_TYPES)

    for script in dir_contents:
        try:
            script_content = script.read_text()
            if not script_content.startswith('#!'):
                continue
        except IOError:
            continue

        script_output = {'plugin': plugin.name, 'filename': str(script)}
        script_output['hash'] = hashlib.sha256(script_content.encode()).hexdigest()
        if not hash_only:
            script_output['content'] = script_content

        results.append(script_output)

    return results


def run_plugin_processing(machine, report_data):
    enabled_reports = Report.objects.all()
    enabled_plugins = Plugin.objects.all()
    enabled_detail_plugins = MachineDetailPlugin.objects.all()
    manager = PluginManager()
    for enabled_plugin in itertools.chain(enabled_reports, enabled_plugins, enabled_detail_plugins):
        plugin = manager.get_plugin_by_name(enabled_plugin.name)
        if plugin:
            plugin.checkin_processor(machine, report_data)


def run_profiles_plugin_processing(machine, profiles_list):
    enabled_plugins = Plugin.objects.all()
    enabled_detail_plugins = MachineDetailPlugin.objects.all()
    manager = PluginManager()
    for enabled_plugin in itertools.chain(enabled_plugins, enabled_detail_plugins):
        plugin = manager.get_plugin_by_name(enabled_plugin.name)
        if plugin:
            plugin.profiles_processor(machine, profiles_list)


def load_default_plugins():
    """Add in default plugins if there are none configured."""
    if not Plugin.objects.exists():
        for order, item in enumerate(PLUGIN_ORDER):
            Plugin.objects.create(name=item, order=order)


def reload_plugins_model():
    """Remove now-absent plugins from db, refresh defaults if needed."""
    if settings.DEBUG:
        logging.getLogger('yapsy').setLevel(logging.WARNING)

    load_default_plugins()
    found = {plugin.name for plugin in PluginManager().get_all_plugins()}
    for model in (Plugin, Report, MachineDetailPlugin):
        _update_plugin_record(model, found)


def _update_plugin_record(model, found):
    """Remove absent plugins

    Args:
        model (plugin subclassing django.db.models.Model): Model to
            refresh and clean.
        found (container): Names of plugins found by yapsy manager.
    """
    all_plugins = model.objects.all()
    # First, clean out all DB plugins that no-longer exist in plugins
    # folder.
    for plugin in all_plugins:
        if plugin.name not in found:
            plugin.delete()


def get_active_and_inactive_plugins(plugin_kind='machines'):
    output = {'active': [], 'inactive': []}
    model = PLUGIN_MODELS[plugin_kind][0]
    plugin_type = PLUGIN_MODELS[plugin_kind][1]

    for plugin in PluginManager().get_all_plugins():
        # Filter out plugins of other types.
        # TODO: This can be cleaned up once old-school plugins are
        # removed.
        if not isinstance(plugin, plugin_type):
            if not isinstance(plugin, OldPluginAdapter):
                continue
            # If there's no type method, assume it's basically Widget.
            elif not hasattr(plugin, 'get_plugin_type') and plugin_type != Widget:
                continue
            # Finally, look up known 'types' in table, assuming it's a
            # Widget if it's an unknown type.
            elif DEPRECATED_PLUGIN_TYPES.get(plugin.get_plugin_type(), Widget) != plugin_type:
                continue

        try:
            db_plugin = model.objects.get(name=plugin.name)
            output['active'].append((plugin, db_plugin))
        except model.DoesNotExist:
            output['inactive'].append(plugin)

    if not model == Report:
        output['active'].sort(key=lambda i: i[1].order)

    return output


def unique_plugin_order(plugin_type='machines'):
    model = PLUGIN_MODELS[plugin_type][0]
    try:
        id_max = model.objects.aggregate(Max('order'))['order__max']
    except KeyError:
        id_max = 0
    return id_max + 1


def get_member_oses(group_type='all', group_id=None):
    """Return a set of all OS families from a group, or ALL OS families.

    The "All" option is to support empty machine groups / business units
    not looking broken or lame.
    """
    if group_type == 'all':
        queryset = Machine.objects.all()
    elif group_type == 'business_unit':
        queryset = Machine.objects.filter(machine_group__business_unit__pk=group_id)
    elif group_type == 'machine_group':
        queryset = Machine.objects.filter(machine_group__pk=group_id)
    else:
        queryset = Machine.objects.filter(pk=group_id)

    if is_postgres():
        queryset = (
            queryset
            .order_by('os_family')
            .distinct('os_family')
            .values_list('os_family', flat=True))
    else:
        queryset = (
            queryset
            .order_by('os_family')
            .values_list('os_family', flat=True)
            .distinct())

    if not queryset:
        queryset = {i[0] for i in OS_CHOICES}

    return queryset


def get_hidden_plugins(group_type='all', group_id=None):
    if group_type == 'all':
        return settings.HIDE_PLUGIN_FROM_FRONT_PAGE

    # remove the plugins that are set to only be shown on the front page
    hidden = settings.LIMIT_PLUGIN_TO_FRONT_PAGE

    # remove the plugins that are to be hidden from this BU
    hidden += [name for name, groups in settings.HIDE_PLUGIN_FROM_BUSINESS_UNIT.items() if group_id
               in groups]

    # remove the plugins that are to be hidden from this Machine Group
    hidden += [name for name, groups in settings.HIDE_PLUGIN_FROM_MACHINE_GROUP.items() if group_id
               in groups]

    return hidden


def order_plugin_output(plugin_data, group_type='all', group_id=None):
    col_width = 12
    total_width = 0

    for item in plugin_data:
        if total_width + item['width'] > col_width:
            item['html'] = '\n</div>\n\n<div class="row">\n' + item['html']
            total_width = item['width']
        else:
            total_width = item['width'] + total_width

    return plugin_data


def get_report_names(plugins):
    return Report.objects.values_list('name', flat=True)


def get_plugin_placeholder_markup(plugins, group_type='all', group_id=None):
    result = []
    manager = PluginManager()
    hidden = get_hidden_plugins(group_type, group_id)
    group_oses = get_member_oses(group_type, group_id)
    display_plugins = [p for p in Plugin.objects.order_by('order') if p.name not in hidden]
    for enabled_plugin in display_plugins:
        name = enabled_plugin.name
        yapsy_plugin = manager.get_plugin_by_name(name)
        if not yapsy_plugin:
            continue
        # Skip this plugin if the group's members OS families aren't supported
        # ...but only if this group has any members (group_oses is not empty
        plugin_os_families = set(yapsy_plugin.get_supported_os_families())
        if group_oses and not plugin_os_families.intersection(group_oses):
            continue
        width = yapsy_plugin.get_widget_width(group_type=group_type, group_id=group_id)
        html = ('<div id="plugin-{}" class="col-md-{}">\n'
                '    <img class="center-block blue-spinner" src="{}"/>\n'
                '</div>\n'.format(name, width, static('img/blue-spinner.gif')))
        result.append({'name': name, 'width': width, 'html': html})

    return order_plugin_output(result, group_type, group_id)


def get_machine_detail_placeholder_markup(machine):
    manager = PluginManager()
    result = []
    for enabled_plugin in MachineDetailPlugin.objects.order_by('order'):
        plugin = manager.get_plugin_by_name(enabled_plugin.name)
        if plugin and machine.os_family in plugin.get_supported_os_families():
            html = ('<div id="plugin-{}">'
                    '    <img class="center-block blue-spinner" src="{}"/>'
                    '</div>'.format(enabled_plugin.name, static('img/blue-spinner.gif')))

            result.append({'name': enabled_plugin.name, 'html': html})

    return result
