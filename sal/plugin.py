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
    """Base class for Sal plugin types to inherit from.

    Public Attributes:
        Meta (obj): Config object plugin configuration attributes.

    Public Methods:
        plugin_type
        supported_os_families
        widget_width
        get_description

        widget_content: Returns rendered content of the plugin.
        get_context: All subclasses need to reimplement this.
    """

    _description = ''
    _plugin_type = 'builtin'
    _supported_os_families = [OSFamilies.darwin]
    _template = ''
    _widget_width = 4

    class Meta(object):
        """Configuration object for plugins

        Specify any of the below attributes to customize the behavior of
        subclasses plugins.

        Attributes:
            description (str): Plugin description. Defaults to ''.
            plugin_type (PluginType): Type of plugin. Defaults to
                'builtin'.
            supported_os_families (list of OSFamilies): OSes this
                plugin can handle. Defaults to [OSFamiles.darwin].
            template (str): Subpath to plugin's template. If not
                specified, will try to use the plugin's class
                name, lowercased, formatted into
                '{name}/templates/{name}.html'.
            widget_width (int): Width of the plugin's widget. Defaults
                to 4.
        """
        description = ''
        plugin_type = PluginTypes.builtin
        supported_os_families = [OSFamilies.darwin]
        template = ''
        widget_width = 4

    def __init__(self):
        super(BasePlugin, self).__init__()
        self.template = loader.get_template(self._get_template())

    def _get_from_meta_or_default(self, name):
        return getattr(self.Meta, name, None) or getattr(self, "_" + name, None)

    def _get_template(self):
        template = self._get_from_meta_or_default('template')
        if not template:
            template = "{0}/templates/{0}.html".format(self.__class__.__name__.lower())
        return template

    def plugin_type(self):
        return self._get_from_meta_or_default('plugin_type')

    def supported_os_families(self):
        return self._get_from_meta_or_default('supported_os_families')

    def widget_width(self):
        return self._get_from_meta_or_default('widget_width')

    def get_description(self):
        return self._get_from_meta_or_default('description')

    def widget_content(self, machines, group_type=None, group_id=None):
        if hasattr(self, 'get_context'):
            context = self.get_context(machines, group_type=group_type, group_id=group_id)
        else:
            context = {}
        return self.template.render(context)

    def get_context(self, machines, group_type=None, group_id=None):
        """Process input into a context suitable for rendering.

        This method must be overridden by subclasses; the base class
        implementation does NOTHING.

        Args:
            machines (QuerySet of Machines or Machine): Machine(s) to
                consider while generating plugin's output.
            group_type (str): One of 'all', 'business_unit',
                'machine_group', or 'machine', determining the limits of
                the machines query. Optional, defaults to None.
            group_id (int): Primary key value of the associated group.
                Optional, defaults to None.

        Returns:
            Dict suitable for plugin's template to render.
        """
        return {}


class MachinesPlugin(BasePlugin):
    """Base class for all dashboard plugins.

    Public_Methods
        filter_machines: Filter passed machines using filter method.
        filter: All subclasses must reimplement this method.
    """

    def filter_machines(self, machines, data):
        machines, data = self.filter(machines, data)
        return machines, data

    def filter(self, machines, data):
        """Filter machines further for redirect to a machine list view

        This method is used when a link originating from the output of
        the plugin needs to redirect to a machine list view. This
        method is then used by the machine list view to filter the
        machines prior to list display.

        All subclasses should reimplement this, as the default
        implementation does nothing.

        Args:
            machines (queryset of Machines): Machines to be filtered.
            data (str): Some value used in the body of this method
                for filtering. Used in the URL by the requesting link.

        Returns:
            Tuple of filtered machines, data.
        """
        return machines, data


class DetailPlugin(BasePlugin):

    _plugin_type = 'machine_detail'


class ReportPlugin(BasePlugin):

    _plugin_type = 'report'


# Load all plugins at import time. Then all plugin users can call
# the `PluginManagerSingleton.get()` classmethod to get a manager that's
# ready to look up plugins.
manager = PluginManagerSingleton.get()
manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
    settings.PROJECT_DIR, 'server/plugins')])
manager.collectPlugins()
