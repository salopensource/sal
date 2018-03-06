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
        widget_width
        get_description
        get_template

        widget_content: Returns rendered content of the plugin.
        get_context: All subclasses need to reimplement this.
    """

    _description = ''
    _plugin_type = 'base'
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
            template (str): Subpath to plugin's template. If not
                specified, will try to use the plugin's class
                name, lowercased, formatted into
                '{name}/templates/{name}.html'.
            widget_width (int): Width of the plugin's widget. Defaults
                to 4.
        """
        pass

    def __init__(self):
        super(BasePlugin, self).__init__()

    def _get_from_meta_or_default(self, name):
        return getattr(self.Meta, name, None) or getattr(self, "_" + name, None)

    def get_template(self, *args, **kwargs):
        """Get the plugin's django template.

        This method by default looks up the self._template attribute.
        If that's not available, it tries to construct a template path
        from the name of the plugin's class, lowercased. (i.e. BasePlugin
        would have a computed template path of
        'baseplugin/templates/baseplugin.html').

        To allow this method to be overridden by clients, it accepts
        *args and **kwargs. See the `widget_content` method to see the
        primary use of this method; it's called with the machines
        queryset, the `group_type`, and `group_id`, so an overriden
        `get_template` could select from different templates based
        on the contextual data.

        Args:
            args: Unused in this implementation.
            kwargs: Unused in this implementation.

        Returns:
            Django template for this plugin.
        """
        template = self._get_from_meta_or_default('template')
        if not template:
            template = "{0}/templates/{0}.html".format(self.__class__.__name__.lower())
        return loader.get_template(template)

    def plugin_type(self):
        return self._get_from_meta_or_default('plugin_type')

    def widget_width(self):
        return self._get_from_meta_or_default('widget_width')

    def get_description(self):
        return self._get_from_meta_or_default('description')

    def widget_content(self, machines, group_type='all', group_id=None):
        context = self.get_context(machines, group_type=group_type, group_id=group_id)
        return self.get_template(machines, group_type, group_id).render(context)

    def get_context(self, machines, group_type, group_id):
        """Process input into a context suitable for rendering.

        This method must be overridden by subclasses; the base class
        implementation does NOTHING.

        Args:
            machines (QuerySet of Machines or Machine): Machine(s) to
                consider while generating plugin's output.
            group_type (str): One of 'all', 'business_unit',
                'machine_group', or 'machine', determining the limits of
                the machines query.
            group_id (int): Primary key value of the associated group.

        Returns:
            Dict suitable for plugin's template to render.
        """
        return {}


class FilterMixin(object):
    """Adds filter_machines method to Plugins

    Public_Methods
        filter_machines: Filter passed machines using filter method.
        filter: All subclasses must reimplement this method.
    """

    def filter_machines(self, machines, data):
        machines, data = self.filter(machines, data)
        return machines, data

    def filter(self, machines, data):
        """Filter machines further for redirect to a machine list view

        This method is used when a link originating from the output of the plugin needs to redirect to a machine list view. This
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


class MachinesPlugin(FilterMixin, BasePlugin):

    _plugin_type = 'builtin'


class DetailPlugin(BasePlugin):
    """Machine Detail plugin class.

    Public Methods:
        supported_os_families
    """
    _plugin_type = 'machine_detail'
    _supported_os_families = [OSFamilies.darwin]

    def supported_os_families(self):
        return self._get_from_meta_or_default('supported_os_families')


class ReportPlugin(FilterMixin, BasePlugin):

    _plugin_type = 'report'
    _widget_width = 12


# Load all plugins at import time. Then all plugin users can call
# the `PluginManagerSingleton.get()` classmethod to get a manager that's
# ready to look up plugins.
manager = PluginManagerSingleton.get()
manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
    settings.PROJECT_DIR, 'server/plugins')])
manager.collectPlugins()
