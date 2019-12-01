"""Plugin classes and helpers

This module contains the base plugin class (`BasePlugin`), from which
the three actual-plugin classes are derived: `Widget`, `DetailPlugin`,
and `ReportPlugin`.

It also provides a manager for locating plugin modules that have been
properly deployed into the Sal plugin directories, with .yapsy info
files.

Finally, an `OSFamilies` class exists simply as a way to protect against
typos in plugin code when specifying OS family names.

Public Classes:
    OSFamilies
    Widget
    DetailPlugin
    ReportPlugin
    PluginManager
"""


import logging
import os

from yapsy.IPlugin import IPlugin
import yapsy.PluginManager

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template import loader

from sal.decorators import handle_access, is_global_admin
from server.models import Machine, Plugin, MachineDetailPlugin, Report
from utils.text_utils import class_to_title


logger = logging.getLogger(__name__)


class OSFamilies():
    chromeos = "ChromeOS"
    darwin = "Darwin"
    linux = "Linux"
    windows = "Windows"


class BasePlugin(IPlugin):
    """Base class for Sal plugin types to inherit from.

    Public Attributes:
        name (str): Name of the class and .yapsy config file `name`.
        title (str): Plugin `name` that is de-camelcased into a display
            name.
        order (int or None): Plugin's display order value (retrieved from
            database), or None if it's not enabled.
        enabled (bool): Whether plugin is enabled for display (retrieved
            from database).
        description (str): Plugin description. Defaults to ''
        only_use_deployed_machines (bool): Plugins normally only show
            deployed machines (the default is True). Set to False to
            tell the plugin to use all machines when calling
            `get_queryset`.
        model (django.db.model): Model plugin should use in its
            `get_queryset` calls.
        supported_os_families (list of str): OS families for which this
            plugin should filter machines by. Defaults to
            `[OSFamilies.darwin, OSFamilies.windows, OSFamilies.linux, OSFamilies.chromeos]`.
        template (str): Relative path to plugin's template file.
            Defaults to '' and plugin will construct a path
            to a default template; see the `get_template` method for
            more information.
        widget_width (int): Plugin's width. Defaults to 4

        Copied from Yapsy config:
        path (str): Path to plugin module on the system.
        copyright (str): Copyright information. Defaults to ''.
        author (str): Name of the author. Defaults to ''.
        website (str): URL to a website. Defaults to ''.
        version (str): Plugin version number. Defaults to '0.1'.

    Public Methods:
        get_widget_width
        get_description
        get_template

        get_queryset

        widget_content: Returns rendered content of the plugin.
        get_context: All subclasses need to reimplement this.
        super_get_context: Call this base classes' get_context.
    """

    _db_model = Plugin
    description = ''
    only_use_deployed_machines = True
    model = Machine
    supported_os_families = [
        OSFamilies.darwin,
        OSFamilies.windows,
        OSFamilies.linux,
        OSFamilies.chromeos
    ]
    template = ''
    widget_width = 4

    def __repr__(self):
        return self.__class__.__name__

    @property
    def name(self):
        return repr(self)

    @property
    def title(self):
        """Return the title of the plugin.

        This uses the class name, broken along capital letters (and
        handling multiple capitals in a row). Subclasses can simply
        declare a `title` str if they just want to set something
        other than the class name.
        """
        return class_to_title(self.__class__.__name__)

    @property
    def enabled(self):
        try:
            self._db_model.objects.get(name=self.name)
            return True
        except self._db_model.DoesNotExist:
            return False

    @property
    def order(self):
        try:
            db_plugin = self._db_model.objects.get(name=self.name)
            return db_plugin.order
        except self._db_model.DoesNotExist:
            return None

    def get_template(self, *args, **kwargs):
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
        if self.template:
            template = self.template
        else:
            # Construct path to templates from plugin's full path.
            template = "{0}/templates/{1}.html".format(
                self.path[:self.path.rfind('/')], self.__class__.__name__.lower())
        return loader.get_template(template)

    def get_supported_os_families(self, **kwargs):
        return self.supported_os_families

    def get_widget_width(self, *args, **kwargs):
        return self.widget_width

    def get_description(self, *args, **kwargs):
        return self.description

    def get_queryset(self, request, **kwargs):
        """Get a filtered queryset for this plugin's Machine model.

        Filters machines to only members of the passed group.
        Filters undeployed machines if deployed is True.
        Filters out machines that don't match this plugin's
        supported_os_families.

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

        # Check access before doing anything else.
        handle_access(request, group_type, group_id)

        queryset = self.model.objects.filter(os_family__in=self.get_supported_os_families())

        # By default, plugins filter out undeployed machines.
        if self.only_use_deployed_machines:
            queryset = self.model.objects.filter(deployed=True)

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
        template = self.get_template(request, **kwargs)
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

    def super_get_context(self, queryset, **kwargs):
        """Helper method to call the base Plugin classes' get_context.
        Yapsy munges the class of instantiated plugins, so you can't
        simply call `super(ClassName, self)...`. This method will dig
        the correct `get_context` out and call it.
        """
        method = eval('super(self.__class__.__bases__[0], self).get_context')
        return method(queryset, **kwargs)

    def checkin_processor(self, machine, report_data):
        """Process checkin data prior to recording in DB.

        The default implementation does nothing.

        Plugins can define a checkin processor method by overriding
        this. This processor is run at the conclusion of the
        client checkin, and includes the report data processed during
        that run.

        Args:
            machine (server.models.Machine): The machine checking in.
            report_data (dict): All of the report data.
        """
        pass

    def profiles_processor(self, machine, profiles_list):
        """Process profiles prior to recording in DB.

        The default implementation does nothing.

        Plugins can define a profiles processor method by overriding
        this. This processor is run at the conclusion of the
        client checkin within the profiles route, and includes the
        complete profile list processed during that run.

        Args:
            machine (server.models.Machine): The machine checking in.
            profiles_list (dict): All of the profiles data.
        """
        pass


class FilterMixin():
    """Adds filter_machines method to Plugins

    Public_Methods
        filter_machines: Filter passed machines using filter method.
        filter: All subclasses must reimplement this method.
    """

    def filter_machines(self, machines, data):
        """Filter machines using plugin's `filter` method.

        Args:
            machines (Queryset of machines): Machines to filter.
            data (str): Some value that `filter` will use to restrict
                queryset by.

        Returns:
            Tuple of filtered machines, data

        Raises:
            Http404 if plugin's `filter` method responds with None, None
        """
        machines, data = self.filter(machines, data)
        if not machines.exists() and not data:
            raise Http404
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


class Widget(FilterMixin, BasePlugin):
    """Represents plugins displayed on the main and group overview pages

    As this is the most basic plugin class, it is simply composed of
    the BasePlugin and FilterMixin classes.
    """

    _db_model = Plugin


class DetailPlugin(BasePlugin):
    """Reports on one machine, displayed on the Machine Detail view."""

    _db_model = MachineDetailPlugin

    def get_queryset(self, request, **kwargs):
        group_id = kwargs.get('group_id', 0)

        # Check access before doing anything else.
        handle_access(request, 'machine', group_id)

        return get_object_or_404(self.model, pk=group_id)


class ReportPlugin(FilterMixin, BasePlugin):
    """Reports are a full page view that show more involved data.

    Reports are appropriate for visualizations that utilize multiple
    charts, built-in menuing, or larger tables.
    """

    _db_model = Report
    widget_width = 12


class PluginManager():
    """Simplifies finding, retrieving, and instantiating plugins

    All plugin instance retrieval should be done through this manager
    rather than by trying to instantiate plugin code manually.

    Please note; this is separate from the database plugin models,
    which track the enablement and ordering of plugins.
    """

    def __init__(self):
        # We can use a PluginManagerSingleton to avoid costly startup
        # and plugin loading.
        self.manager = yapsy.PluginManager.PluginManagerSingleton.get()
        # No need to recollect if it has already been done.
        if not self.manager.category_mapping.get('Default'):
            self.manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
                settings.PROJECT_DIR, 'server/plugins')])
            self.manager.collectPlugins()

    def get_plugin_by_name(self, name):
        """Search the configured plugin sources for a plugin, by name.

        Args:
            name (str): Name of plugin (from .yapsy file), and the name
                of the plugin class.

        Returns:
            Widget, Report, or DetailPlugin instance, or None if no
            plugin was found with this name.
        """
        plugin = self.manager.getPluginByName(name)
        if plugin:
            plugins = self._process_plugins([plugin])
            return plugins[0] if plugins else None

    def get_all_plugins(self):
        """Return a list of all plugins found in configured directories.

        This returns plugins of all types; if they're in the configured
        plugin directory, they will be returned.

        Unlike the Yapsy plugin manager, this method returns just
        Widget, ReportPlugin, and DetailPlugin instances.

        Returns:
            List of Widget, ReportPlugin, and DetailPlugin instances.
        """
        return self._process_plugins(self.manager.getAllPlugins())

    def _process_plugins(self, plugins):
        """Copy attributes to plugin object and throw away the outer layer

        Args:
            plugins (BasePlugin): Plugins found by the manager.

        Returns:
            List of plugins.
        """
        extracted = []
        for plugin in plugins:
            if plugin.plugin_object:
                # Embed the attributes from the IPluginInfo container on the
                # plugin instance, and just return those.
                for attribute in ('path', 'copyright', 'author', 'website', 'version'):
                    setattr(plugin.plugin_object, attribute, getattr(plugin, attribute))

                extracted.append(plugin.plugin_object)

        return extracted
