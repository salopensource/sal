import hashlib
import json
import logging
import os
import plistlib
import time
import xml.etree.ElementTree as ET
from distutils.version import LooseVersion
from itertools import chain

import requests

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404

from sal.decorators import is_global_admin
from sal.plugin import BasePlugin, MachinesPlugin, OldPluginWrapper, PluginManager
from server.models import *


PLUGIN_ORDER = [
    'Activity', 'Status', 'OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory', 'DiskSpace',
    'PendingAppleUpdates', 'Pending3rdPartyUpdates', 'Encryption', 'Gatekeeper', 'Sip',
    'XprotectVersion']
TRUTHY = {'TRUE', 'YES'}
FALSY = {'FALSE', 'NO'}
STRINGY_BOOLS = TRUTHY.union(FALSY)
TWENTY_FOUR_HOURS = 86400


def safe_unicode(s):
    if isinstance(s, unicode):
        return s.encode('utf-8', errors='replace')
    else:
        return s


def get_server_version():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    version = plistlib.readPlist(os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist'))
    return version['version']


def get_current_release_version_number():
    """Get the currently available Sal version.

    Returns:
        (str) Version number if it could be retrieved, otherwise None.
    """
    current_version = None
    try:
        response = requests.get('https://version.salopensource.com')
        if response.status_code == 200:
            current_version = response.text
    except requests.exceptions.RequestException:
        pass
    return current_version


def get_install_type():
    if os.path.exists('/home/docker'):
        return 'docker'
    else:
        return 'bare'


def send_report():
    """Send report data if last report was sent over 24 hours ago.

    Returns:
        (str) current Sal version number or None if there was a problem
        retrieving it. This will return regardless of whether the report
        needed to be sent.
    """
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
        version = plistlib.readPlist(
            os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist'))
        output['version'] = version['version']
        # plist encode output
        post_data = plistlib.writePlistToString(output)
        response = requests.post('https://version.salopensource.com', data={"data": post_data})
        set_setting('last_sent_data', int(current_time))
        print response.status_code
        if response.status_code == 200:
            return response.text
        else:
            return None
    else:
        return get_current_release_version_number()


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
    # Grab this from the database so we're not making requests all
    # the time.
    current_release_version = get_setting('current_version', '0')

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


def stringify(data):
    """Sanitize collection data into a string format for db storage.

    Args:
        data (str, bool, numeric, dict, list): Condition values to
            squash into strings.

    Returns:
        list data returns as a comma separated string or '{EMPTY}'
        if the list is empty.

        All other data types are `str()` converted, including nested
        collections in a list.
    """
    if isinstance(data, list):
        return ", ".join(str(i) for i in data) if data else "{EMPTY}"

    # Handle dict, int, float, bool values.
    return str(data)


def is_postgres():
    postgres_backend = 'django.db.backends.postgresql_psycopg2'
    db_setting = settings.DATABASES['default']['ENGINE']
    return db_setting == postgres_backend


def decode_to_string(data, compression='base64bz2'):
    '''Decodes a string that is optionally bz2 compressed and always base64 encoded.'''
    if compression == 'base64bz2':
        try:
            bz2data = base64.b64decode(data)
            return bz2.decompress(bz2data)
        except Exception:
            return ''
    elif compression == 'base64':
        try:
            return base64.b64decode(data)
        except Exception:
            return
            ''

    return ''


def friendly_machine_model(machine):
    # See if the machine's model already has one (and only one) friendly name
    output = None
    friendly_names = Machine.objects.filter(machine_model=machine.machine_model).\
        values('machine_model_friendly').\
        annotate(num_models=Count('machine_model_friendly', distinct=True)).distinct()
    for name in friendly_names:
        if name['num_models'] == 1:
            output = name['machine_model_friendly']
            break

    if not output and not machine.serial.startswith('VM') and machine.os_family == 'Darwin':
        if len(machine.serial) == 12:
            serial_snippet = machine.serial[-4:]
        else:
            # older models product code is the last three characters of the serial
            serial_snippet = machine.serial[-3:]
        payload = {'cc': serial_snippet}
        output = None
        try:
            r = requests.get('http://support-sp.apple.com/sp/product', params=payload)
        except requests.exceptions.RequestException as e:
            print machine.serial
            print e

        try:
            output = ET.fromstring(r.text).find('configCode').text
        except Exception:
            print 'Did not receive a model name for %s, %s. Error:' % (
                machine.serial, machine.machine_model)

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


# Plugin utilities

def process_plugin_script(results, machine):
    rows_to_create = []

    results = get_newest_plugin_results(results)

    for plugin in results:
        plugin_name = plugin['plugin']
        historical = plugin.get('historical', False)
        if not historical:
            PluginScriptSubmission.objects.filter(
                machine=machine, plugin=safe_unicode(plugin_name)).delete()

        plugin_script = PluginScriptSubmission(
            machine=machine, plugin=safe_unicode(plugin_name), historical=historical)
        plugin_script.save()
        data = plugin.get('data')
        for key, value in data.items():
            plugin_row = PluginScriptRow(
                submission=safe_unicode(plugin_script),
                pluginscript_name=safe_unicode(key),
                pluginscript_data=safe_unicode(value),
                submission_and_script_name=(safe_unicode('{}: {}'.format(plugin_name, key))))
            if is_postgres():
                rows_to_create.append(plugin_row)
            else:
                plugin_row.save()

    if is_postgres():
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
        plugin (yapsy.PluginInfo): Plugin returned from a PluginManager.
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
    plugin_path = os.path.join(plugin.path, 'scripts')
    server_path = os.path.abspath(os.path.join(plugin.path, '..', 'scripts'))
    if os.path.exists(plugin_path):
        scripts_dir = plugin_path
    elif os.path.exists(server_path):
        scripts_dir = server_path
    else:
        return results

    if script_name:
        dir_contents = [script_name]
    else:
        dir_contents = os.listdir(scripts_dir)

    for script in dir_contents:
        path = os.path.join(scripts_dir, script)
        try:
            with open(path, "r") as script_handle:
                script_content = script_handle.read()

            if not script_content.startswith('#!'):
                continue
        except IOError:
            continue

        script_output = {'plugin': plugin.name, 'filename': script}
        script_output['hash'] = hashlib.sha256(script_content).hexdigest()
        if not hash_only:
            script_output['content'] = script_content

        results.append(script_output)

    return results


def run_plugin_processing(machine, report_data):
    yapsy_plugins = PluginManager().get_all_plugins()

    enabled_reports = Report.objects.all()
    for enabled_report in enabled_reports:
        for plugin in yapsy_plugins:
            if enabled_report.name == plugin.name:
                # Not all plugins will have a checkin_processor
                try:
                    plugin.plugin_object.checkin_processor(machine, report_data)
                except Exception:
                    pass

    # Get all the enabled plugins
    enabled_plugins = Plugin.objects.all()
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in yapsy_plugins:
            # Not all plugins will have a checkin_processor
            try:
                plugin.plugin_object.checkin_processor(machine, report_data)
            except Exception:
                pass

    # Get all the enabled plugins
    enabled_plugins = MachineDetailPlugin.objects.all()
    for enabled_plugin in enabled_plugins:
        # Loop round the plugins and print their names.
        for plugin in yapsy_plugins:
            # Not all plugins will have a checkin_processor
            try:
                plugin.plugin_object.checkin_processor(machine, report_data)
            except Exception:
                pass


def load_default_plugins():
    """Add in default plugins if there are none configured."""
    if not Plugin.objects.exists():
        for order, item in enumerate(PLUGIN_ORDER):
            Plugin.objects.create(name=item, order=order)


def reload_plugins_model():
    """Set plugin types and descriptions, and remove now-absent from db."""
    if settings.DEBUG:
        logging.getLogger('yapsy').setLevel(logging.WARNING)

    load_default_plugins()

    yapsy_plugins = PluginManager().get_all_plugins()
    found = {plugin.name for plugin in yapsy_plugins}

    for model in (Plugin, Report, MachineDetailPlugin):
        _update_plugin_record(model, yapsy_plugins, found)


def _update_plugin_record(model, yapsy_plugins, found):
    """Remove absent plugins, and refresh plugin type and description.

    Values are validated prior to saving, and will log errors.

    Args:
        model (plugin subclassing django.db.models.Model): Model to
            refresh and clean.
        yapsy_plugins (list): Loaded plugins from yapsy manager.
        found (container): Names of plugins found by yapsy manager.
    """
    all_plugins = model.objects.all()
    # First, clean out all DB plugins that no-longer exist in plugins
    # folder.
    for plugin in all_plugins:
        if plugin.name not in found:
            plugin.delete()

    for plugin in yapsy_plugins:
        try:
            dbplugin = all_plugins.get(name=plugin.name)
        except model.DoesNotExist:
            continue

        plugin_object = plugin.plugin_object
        if not isinstance(plugin_object, BasePlugin):
            plugin_object = OldPluginWrapper(plugin_object)

        if hasattr(model, 'type'):
            try:
                # TODO: Investigate whether we should include the request in this call.
                declared_type = plugin.plugin_object.get_plugin_type(None)
            except AttributeError:
                declared_type = model._meta.get_field('type').default

            dbplugin.type = declared_type

        # TODO: Investigate whether we should include the request in this call.
        dbplugin.description = plugin_object.get_description(None)

        try:
            dbplugin.full_clean()
            dbplugin.save()
        except ValidationError as err:
            print "Plugin: '{}' could not be validated due to error(s): '{}', removing.".format(
                dbplugin.name, ", ".join(err.messages))


def disabled_plugins(plugin_kind='main'):
    plugin_models = {'main': (Plugin, 'builtin'), 'report': (Report, 'report'),
                     'machine_detail': (MachineDetailPlugin, 'machine_detail')}
    output = []

    for plugin in PluginManager().get_all_plugins():
        plugin_type = plugin.plugin_object.get_plugin_type(None)

        # Filter out plugins of other types.
        if plugin_type != plugin_models[plugin_kind][1]:
            continue

        model, _ = plugin_models.get(plugin_kind, (None, None))
        if model:
            try:
                model.objects.get(name=plugin.name)
            except model.DoesNotExist:
                item = {}
                item['name'] = plugin.name
                if model == MachineDetailPlugin:
                    try:
                        supported_os_families = plugin.plugin_object.get_supported_os_families()
                    except AttributeError:
                        supported_os_families = ['Darwin', 'Windows', 'Linux', 'ChromeOS']
                    item['os_families'] = supported_os_families

                output.append(item)

    return output


def unique_plugin_order(plugin_type='builtin'):
    if plugin_type == 'builtin':
        plugins = Plugin.objects.all()
    elif plugin_type == 'report':
        plugins = Report.objects.all()
    elif plugin_type == 'machine_detail':
        plugins = MachineDetailPlugin.objects.all()
    else:
        plugins = Plugin.objects.all()
    id_max = plugins.aggregate(Max('order'))['order__max']
    id_next = id_max + 1 if id_max else 1
    return id_next


def order_plugin_output(pluginOutput, page='front', theID=None):
    output = pluginOutput
    if page == 'front':
        # remove the plugins that are in the list
        for item in output:
            for key in settings.HIDE_PLUGIN_FROM_FRONT_PAGE:
                if item['name'] == key:
                    output.remove(item)

    if page != 'front':
        if page == 'bu_dashboard':
            business_unit = get_object_or_404(BusinessUnit, pk=theID)
            for item in output:
                # remove the plugins that are to be hidden from this BU
                for key, ids in settings.HIDE_PLUGIN_FROM_BUSINESS_UNIT.iteritems():
                    if item['name'] == key:
                        if str(theID) in ids:
                            output.remove(item)
                # remove the plugins that are set to only be shown on the front page
                for key in settings.LIMIT_PLUGIN_TO_FRONT_PAGE:
                    if item['name'] == key:
                        output.remove(item)

        if page == 'group_dashboard':
            machine_group = get_object_or_404(MachineGroup, pk=theID)
            # get the group's BU.
            business_unit = machine_group.business_unit
            for item in output:
                for key, ids in settings.HIDE_PLUGIN_FROM_BUSINESS_UNIT.iteritems():
                    if item['name'] == key:
                        if str(business_unit.id) in ids:
                            output.remove(item)
                # remove the plugins that are to be hidden from this Machine Group
                for key, ids in settings.HIDE_PLUGIN_FROM_MACHINE_GROUP.iteritems():
                    if item['name'] == key:
                        if str(theID) in ids:
                            output.remove(item)

                # remove the plugins that are set to only be shown on the front page
                for key in settings.LIMIT_PLUGIN_TO_FRONT_PAGE:
                    if item['name'] == key:
                        output.remove(item)
    # Loop over all of the items, their width will have been returned
    col_width = 12
    total_width = 0
    counter = 0
    # length of the output, but starting at 0, so subtract one
    length = len(output) - 1
    # We don't do any of this for machine detail
    if page != 'machine_detail':
        for item in output:
            # if we've gone through all the items, just stop
            if counter >= length:
                break
            # No point doing anything if the plugin isn't going to return any output
            if int(item['width']) != 0:
                if total_width + item['width'] > col_width:
                    item['html'] = '\n</div>\n\n<div class="row">\n' + item['html']
                    # print 'breaking'
                    total_width = item['width']
                    needs_break = False  # noqa: F841
                else:
                    total_width = int(item['width']) + total_width
            counter = counter + 1
            # print item['name']+' total: '+str(total_width)
    return output


def get_report_data(plugins):
    return Report.objects.values_list('name', flat=True)


def get_plugin_data(plugins, page='front', the_id=None):
    result = []
    manager = PluginManager()

    for enabled_plugin in Plugin.objects.order_by('order'):
        name = enabled_plugin.name
        yapsy_plugin = manager.get_plugin_by_name(name)
        plugin_object = yapsy_plugin.plugin_object
        width = plugin_object.get_widget_width(None)
        html = ('<div id="plugin-{}" class="col-md-{}">\n'
                '    <img class="center-block blue-spinner" src="{}"/>\n'
                '</div>\n'.format(name, width, static('img/blue-spinner.gif')))
        result.append({'name': name, 'width': width, 'html': html})

    return order_plugin_output(result, page, the_id)


def get_machine_detail_plugin_data(machine):
    result = []
    yapsy_plugins = {
        p.name: p for p in PluginManager().get_all_plugins()
        # TODO (sheagcraig): This used to be excluding 'builtin' and 'full_page',
        # but I assumed that `full_page` at some point became `report`.
        if p.plugin_object.get_plugin_type(None) not in ('builtin', 'report') and
        machine.os_family in p.plugin_object.get_supported_os_families()}

    for enabled_plugin in MachineDetailPlugin.objects.order_by('order'):
        name = enabled_plugin.name
        yapsy_plugin = yapsy_plugins.get(name)
        if yapsy_plugin:
            html = ('<div id="plugin-{}">'
                    '    <img class="center-block blue-spinner" src="{}"/>'
                    '</div>'.format(name, static('img/blue-spinner.gif')))

            result.append({'name': name, 'html': html})

    return order_plugin_output(result, 'machine_detail')
