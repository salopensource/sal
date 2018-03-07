import logging
import os
import re

from yapsy.IPlugin import IPlugin
import yapsy.PluginManager

from django.shortcuts import get_object_or_404
from django.template import loader

from sal import settings
from sal.decorators import handle_access, is_global_admin
from server.models import Machine


DEPRECATED_PAGES = {
    'all': 'front', 'business_unit': 'bu_dashboard', 'machine_group': 'group_dashboard',
    'machine': 'machine_detail'}


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

    description = ''
    model = Machine
    plugin_type = 'base'
    template = ''
    widget_width = 4

    @property
    def title(self):
        """Return the title of the plugin.

        This uses the class name, broken along capital letters (and
        handling multiple capitals in a row). Subclasses can simply
        declare a `title` str if they just want to set something
        other than the class name.
        """
        return class_to_title(self.__class__.__name__)

    def get_template(self, **kwargs):
        """Get the plugin's django template.

        This method by default looks up the template attribute.
        If that's not available, it tries to construct a template path
        from the name of the plugin's class, lowercased. (i.e. BasePlugin
        would have a computed template path of
        'baseplugin/templates/baseplugin.html').

        To allow this method to be overridden by clients, it accepts
        **kwargs. See the `widget_content` method to see the
        primary use of this method; it's called with the machines
        queryset, the `group_type`, and `group_id`, so an overriden
        `get_template` could select from different templates based
        on the contextual data.

        Args:
            kwargs: Unused in this implementation.

        Returns:
            Django template for this plugin.
        """
        template = self.template if self.template else "{0}/templates/{0}.html".format(
            self.__class__.__name__.lower())
        return loader.get_template(template)

    # TODO: This is on the chopping block.
    def get_plugin_type(self, request, **kwargs):
        return self.plugin_type

    def get_widget_width(self, request, **kwargs):
        return self.widget_width

    def get_description(self, request, **kwargs):
        return self.description

    def get_queryset(self, request, **kwargs):
        """Get a filtered queryset for this plugin's Machine model.

        Args:
            request (Request): The request passed from the View.
            **kwargs: Expected kwargs follow
                group_type (str): One of 'all' (the default),
                    'business_unit', or 'machine_group'.
                group_id (int, str): ID of the group_type's object to
                    filter by. Default to 0.
                deployed (bool): Filter by Machine.deployed. Defaults
                    to True.

        Returns:
            Filtered queryset.
        """
        group_type = kwargs.get('group_type', 'all')
        group_id = kwargs.get('group_id', 0)
        deployed = kwargs.get('deployed', True)

        # Check access before doing anything else.
        handle_access(request, group_type, group_id)

        # By default, plugins filter out undeployed machines.
        queryset = self.model.objects.filter(deployed=deployed)

        if group_type == "business_unit":
            queryset = queryset.filter(machine_group__business_unit__pk=group_id)
        elif group_type == "machine_group":
            queryset = queryset.filter(machine_group__pk=group_id)
        elif is_global_admin(request.user):
            # GA users won't have business units, so just do nothing.
            pass
        else:
            # The 'all' / 'front' type is being requested.
            queryset = queryset.filter(
                machine_group__business_unit__in=request.user.businessunit_set.all())

        return queryset

    def widget_content(self, request, **kwargs):
        queryset = self.get_queryset(request, **kwargs)
        context = self.get_context(queryset, **kwargs)
        template = self.get_template(**kwargs)
        return template.render(context)

    def get_context(self, queryset, **kwargs):
        """Process input into a context suitable for rendering.

        This method must be overridden by subclasses; You can't call
        super on this because of the way yapsy constructs the instance.

        Args:
            queryset (QuerySet of Machines or Machine): Machine(s) to
                consider while generating plugin's output.
            **kwargs: (Expected keys below)
            group_type (str): One of 'all', 'business_unit',
                'machine_group', or 'machine', determining the limits of
                the machines query.
            group_id (int): Primary key value of the associated group.

        Returns:
            Dict suitable for plugin's template to render. Default
            implementation returns the method's **kwargs, and adds in
            the plugin itself with key 'plugin'.
        """
        kwargs['plugin'] = self
        return kwargs

    def super_context(self, queryset, **kwargs):
        """Helper method to call the base Plugin classes' get_context.
        Yapsy munges the class of instantiated plugins, so you can't
        simply call `super(ClassName, self)...`. This method will dig
        the correct `get_context` out and call it.
        """
        method = eval('super(self.__class__.__bases__[0], self).get_context')
        return method(queryset, **kwargs)


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


class MachinesPlugin(FilterMixin, BasePlugin):

    plugin_type = 'builtin'


class DetailPlugin(BasePlugin):
    """Machine Detail plugin class.

    Public Methods:
        supported_os_families
    """
    plugin_type = 'machine_detail'
    supported_os_families = [OSFamilies.darwin]

    def get_supported_os_families(self, **kwargs):
        return self.supported_os_families

    def get_queryset(self, request, **kwargs):
        group_id = kwargs.get('group_id', 0)

        # Check access before doing anything else.
        handle_access(request, 'machine', group_id)

        return get_object_or_404(self.model, pk=group_id)


class ReportPlugin(FilterMixin, BasePlugin):

    plugin_type = 'report'
    widget_width = 12


class OldPluginWrapper(BasePlugin):
    """Provides current Plugin interface by wrapping old-style plugin"""

    model = Machine

    def __init__(self, plugin):
        self.plugin = plugin

    def get_template(self, **kwargs):
        return None

    def get_plugin_type(self, request, **kwargs):
        try:
            return self.plugin.plugin_type()
        except AttributeError:
            return 'builtin'

    def get_widget_width(self, request, **kwargs):
        return self.plugin.widget_width()

    def get_description(self, request, **kwargs):
        try:
            return self.plugin.get_description()
        except AttributeError:
            return ""

    def get_supported_os_families(self):
        if hasattr(self.plugin, 'supported_os_families'):
            return self.plugin.supported_os_families()

        return [OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        return {}

    def get_queryset(self, request, **kwargs):
        # Override BasePlugin get_queryset to return a single machine
        # instead of a Queryset. This is mostly just here to avoid
        # having to create a bunch of support wrapper subclasses
        # when this stuff is going away anyway.
        queryset = super(OldPluginWrapper, self).get_queryset(request, **kwargs)
        if self.get_plugin_type(request, **kwargs) == 'machine_detail':
            queryset = queryset[0]
        return queryset

    def widget_content(self, request, **kwargs):
        group_type = kwargs.get('group_type', 'all')
        # Old plugins expect the page name 'front'.
        group_type = DEPRECATED_PAGES[group_type]
        group_id = kwargs.get('group_id', 0)
        queryset = self.get_queryset(request, **kwargs)
        # Calling convention was different back then...
        return self.plugin.widget_content(group_type, queryset, group_id)


class PluginManager(object):

    def __init__(self):
        self.manager = yapsy.PluginManager.PluginManager()
        self.manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
            settings.PROJECT_DIR, 'server/plugins')])
        self.manager.collectPlugins()

    def get_plugin_by_name(self, name):
        plugin = self.wrap_old_plugins([self.manager.getPluginByName(name)])[0]
        return plugin

    def get_all_plugins(self):
        return self.wrap_old_plugins(self.manager.getAllPlugins())

    def wrap_old_plugins(self, plugins):
        wrapped = []
        for plugin in plugins:
            if plugin.plugin_object and not isinstance(plugin.plugin_object, BasePlugin):
                logging.warning(
                    "Plugin '%s' needs to be updated to subclass a Sal Plugin!", plugin.name)
                plugin.plugin_object = OldPluginWrapper(plugin.plugin_object)
            wrapped.append(plugin)
        return wrapped


def class_to_title(text):
    return re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', text)
