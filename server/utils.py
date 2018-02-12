import hashlib
import logging
import os
import plistlib
import time
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
import requests
from yapsy.PluginManager import PluginManager

from server.models import *


PLUGIN_ORDER = [
    'Activity', 'Status', 'OperatingSystem', 'MunkiVersion', 'Uptime', 'Memory', 'DiskSpace',
    'PendingAppleUpdates', 'Pending3rdPartyUpdates', 'Encryption', 'Gatekeeper', 'Sip',
    'XprotectVersion']


def safe_unicode(s):
    if isinstance(s, unicode):
        return s.encode('utf-8', errors='replace')
    else:
        return s


def csvrelated(header_item, facts, kind):
    found = False
    if kind == 'facter':
        for fact in facts:
            try:
                if header_item == 'Facter: ' + fact['fact_name']:
                    found = True
                    return fact['fact_data']
            except Exception:
                pass
    elif kind == 'condition':
        for condition in facts:
            try:
                if header_item == 'Munki Condition: ' + condition['condition_name']:
                    found = True
                    return condition['condition_data']
            except Exception:
                pass
    elif kind == 'pluginscript':
        for pluginscriptrow in facts:
            try:
                if header_item == pluginscriptrow['submission_and_script_name']:
                    found = True
                    return pluginscriptrow['pluginscript_data']
            except Exception:
                pass
    if not found:
        return ''


def get_version_number():
    # See if we're sending data
    try:
        senddata_setting = SalSetting.objects.get(name='send_data')
    except SalSetting.DoesNotExist:
        # it's not been set up yet, just return true
        return True

    try:
        last_sent = SalSetting.objects.get(name='last_sent_data')
    except SalSetting.DoesNotExist:
        last_sent = SalSetting(name='last_sent_data', value='0')
        last_sent.save()

    current_time = int(time.time())
    if int(last_sent.value) < (current_time - 86400) or int(last_sent.value) == 0:
        try:
            current_version = SalSetting.objects.get(name='current_version')
        except SalSetting.DoesNotExist:
            current_version = SalSetting(name='current_version', value='0')
            current_version.save()
        last_sent.value = current_time
        last_sent.save()
        if senddata_setting.value == 'yes':
            version = send_report()
            current_version.value = version
            current_version.save()
        else:
            try:
                r = requests.get('https://version.salopensource.com')
                if r.status_code == 200:
                    current_version.value = r.text
                    current_version.save()
            except Exception:
                return True


def get_install_type():
    if os.path.exists('/home/docker'):
        return 'docker'
    else:
        return 'bare'


def send_report():
    output = {}
    # get total number of machines
    output['machines'] = Machine.objects.all().count()
    # get list of plugins
    plugins = []
    for plugin in Plugin.objects.all():
        plugins.append(plugin.name)

    for plugin in Report.objects.all():
        plugins.append(plugin.name)
    output['plugins'] = plugins
    # get install type
    output['install_type'] = get_install_type()
    # get database type
    output['database'] = settings.DATABASES['default']['ENGINE']

    # version
    current_dir = os.path.dirname(os.path.realpath(__file__))
    version = plistlib.readPlist(os.path.join(os.path.dirname(current_dir), 'sal', 'version.plist'))
    output['version'] = version['version']
    # plist encode output
    post_data = plistlib.writePlistToString(output)
    r = requests.post('https://version.salopensource.com', data={"data": post_data})
    print r.status_code
    if r.status_code == 200:
        return r.text
    else:
        return 'Error'


def listify_condition_data(data):
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
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        return True
    else:
        return False


def flatten_and_sort_list(the_list):
    output = ''
    counter = 1
    for item in sorted(the_list):
        if counter == 1:
            output = item
        else:
            output = output + ', ' + item
        counter += 1
    return output


def getBUmachines(theid):
    business_unit = get_object_or_404(BusinessUnit, pk=theid)
    machines = Machine.objects.filter(machine_group__business_unit=business_unit)

    return machines


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
    else:
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

    if not output and not machine.serial.startswith('VM'):
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


# Plugin utilities

def get_all_plugins():
    """Get all plugins from the yapsy manager."""
    # Build the manager
    manager = PluginManager()
    # Tell it the default place(s) where to find plugins
    manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
        settings.PROJECT_DIR, 'server/plugins')])
    # Load all plugins
    manager.collectPlugins()
    return manager.getAllPlugins()


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
                submission_and_script_name=(
                    safe_unicode(
                        plugin_name + ': ' + key)))
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
    # Try to get all files in the plugins 'scripts' dir

    script_output = None
    if os.path.exists(os.path.join(plugin.path, 'scripts')):
        scripts_dir = os.path.join(plugin.path, 'scripts')
    elif os.path.exists(os.path.abspath(os.path.join(os.path.join(plugin.path), '..', 'scripts'))):
        scripts_dir = os.path.abspath(os.path.join(
            os.path.join(plugin.path), '..', 'scripts'))
    else:
        return None

    for script in os.listdir(scripts_dir):
        if script_name:
            if script_name != script:
                break
        script_content = open(os.path.join(scripts_dir, script), "r").read()
        script_output = {}
        if not hash_only:
            script_output['content'] = script_content
        script_output['plugin'] = plugin.name
        script_output['filename'] = script
        script_output['hash'] = hashlib.sha256(script_content).hexdigest()
        return script_output


def run_plugin_processing(machine, report_data):
    yapsy_plugins = get_all_plugins()

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

    yapsy_plugins = get_all_plugins()
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
    all_plugins = getattr(model, 'objects').all()
    for plugin in all_plugins:
        if plugin.name not in found:
            plugin.delete()

    for plugin in yapsy_plugins:
        try:
            dbplugin = all_plugins.get(name=plugin.name)
        except model.DoesNotExist:
            continue

        if hasattr(model, 'type'):
            try:
                declared_type = plugin.plugin_object.plugin_type()
            except AttributeError:
                declared_type = model._meta.get_field('type').default

            dbplugin.type = declared_type

        try:
            dbplugin.description = plugin.plugin_object.get_description()
        except AttributeError:
            dbplugin.description = ''

        try:
            dbplugin.full_clean()
            dbplugin.save()
        except ValidationError as err:
            print "Plugin: '{}' could not be validated due to error(s): '{}', removing.".format(
                dbplugin.name, ", ".join(err.messages))


def disabled_plugins(plugin_kind='main'):
    plugin_models = {'main': Plugin, 'report': Report, 'machine_detail': MachineDetailPlugin}
    output = []

    for plugin in get_all_plugins():
        try:
            plugin_type = plugin.plugin_object.plugin_type()
        except AttributeError:
            plugin_type = None

        try:
            supported_os_families = plugin.plugin_object.supported_os_families()
        except AttributeError:
            supported_os_families = ['Darwin', 'Windows', 'Linux']

        model = plugin_models.get(plugin_type)
        if model:
            try:
                model.objects.get(name=plugin.name)
            except model.DoesNotExist:
                item = {}
                item['name'] = plugin.name
                item['os_families'] = supported_os_families
                output.append(item)

    return output


def UniquePluginOrder(plugin_type='builtin'):
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


def orderPlugins(output):
    # Sort by name initially
    output = sorted(output, key=lambda k: k['name'])
    # Order by the list specified in settings
    # Run through all of the names in pluginOutput.
    # If they're not in the PLUGIN_ORDER list, we'll add them to a new one
    not_ordered = []
    for item in output:
        if item['name'] not in settings.PLUGIN_ORDER:
            not_ordered.append(item['name'])

    search_items = settings.PLUGIN_ORDER + not_ordered
    lookup = {s: i for i, s in enumerate(search_items)}
    output = sorted(output, key=lambda o: lookup[o['name']])
    return output


def orderPluginOutput(pluginOutput, page='front', theID=None):
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
