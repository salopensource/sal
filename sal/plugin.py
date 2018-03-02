import os

from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManagerSingleton

from django.template import loader

from sal import settings


class OSFamilies(object):
    chromeos = "ChromeOS"
    darwin = "Darwin"
    linux = "Linux"
    windows = "Windows"


class PluginTypes(object):
    builtin = "builtin"
    machine_detail = "machine_detail"
    report = "report"


class BasePlugin(IPlugin):

    _description = ''
    _plugin_type = 'builtin'
    _supported_os_families = [OSFamilies.darwin]
    _template = ''
    _widget_width = 4

    class Meta(object):
        description = ''
        plugin_type = PluginTypes.builtin
        supported_os_families = [OSFamilies.darwin]
        template = ''
        widget_width = 4

    def __init__(self):
        super(BasePlugin, self).__init__()
        self.template = loader.get_template(self.get_template())

    def _get_from_meta_or_default(self, name):
        return getattr(self.Meta, name, None) or getattr(self, "_" + name, None)

    def get_template(self):
        return self._get_from_meta_or_default('template')

    def plugin_type(self):
        return self._get_from_meta_or_default('plugin_type')

    def supported_os_families(self):
        return self._get_from_meta_or_default('supported_os_families')

    def widget_width(self):
        return self._get_from_meta_or_default('widget_width')

    def get_description(self):
        return self._get_from_meta_or_default('description')

    def widget_content(self, page, machines=None, instance_id=None):
        context = {}
        if hasattr(self, 'process'):
            context = self.process(page, machines, instance_id)
        return self.template.render(context)


class MachinesPlugin(BasePlugin):

    def filter_machines(self, machines, data):
        if hasattr(self, 'filter'):
            machines = self.filter(machines, data)
        return machines, data


class MachineDetailPlugin(BasePlugin):

    _plugin_type = 'machine_detail'


class ReportPlugin(BasePlugin):

    _plugin_type = 'report'


manager = PluginManagerSingleton.get()
manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
    settings.PROJECT_DIR, 'server/plugins')])
manager.collectPlugins()
