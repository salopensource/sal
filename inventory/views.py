# standard library
import collections
import copy
import hashlib
import itertools
from distutils.version import LooseVersion
from urllib.parse import quote

# Django
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, View

# 3rd Party Django
from datatableview import Datatable
from datatableview.columns import DisplayColumn
from datatableview.views import DatatableView

# local Django
import server.utils
import utils.csv
from inventory.models import Application, Inventory, InventoryItem
from sal.decorators import (class_login_required, class_access_required, key_auth_required)
from server.models import BusinessUnit, MachineGroup, Machine
from utils import text_utils


INVENTORY_PATTERN = server.utils.get_setting('inventory_exclusion_pattern')
FILTER_VIRTUAL = server.utils.get_setting('filter_proxied_virtualization_apps', True)

ApplicationTuple = collections.namedtuple(
    'Application', ['name', 'bundleid', 'bundlename', 'install_count'])


# Generate the fields dict needed for our CSV row generator.
APPLICATION_FIELDS = dict(itertools.zip_longest(ApplicationTuple._fields, []))


class GroupMixin():
    """Mixin to add get_business_unit method for access decorators.

    The view must have the URL configured so that kwargs for
    group_type and group_id are present.

    At this time, the classes listed in the classes dict below are
    supported.
    """
    classes = {"all": None,
               "business_unit": BusinessUnit,
               "machine": Machine,
               "machine_group": MachineGroup}
    access_filter = {
        Application: {
            BusinessUnit: "inventoryitem__machine__machine_group__business_unit",
            MachineGroup: "inventoryitem__machine__machine_group",
            Machine: "inventoryitem__machine", },
        InventoryItem: {
            BusinessUnit: "machine__machine_group__business_unit",
            MachineGroup: "machine__machine_group",
            Machine: "machine", },
        Machine: {
            BusinessUnit: "machine_group__business_unit",
            MachineGroup: "machine_group",
            Machine: "", },
        Inventory: {}, }

    model = None

    @classmethod
    def get_business_unit(cls, group_type='all', group_id=None, **kwargs):
        """Return the business unit associated with this request.

        Args:
            group_type (str): One of: 'all', 'business_unit', 'machine',
                or 'machine_group'.
            group_id (int): ID number of the group, or None.

        Returns:
            BusinessUnit instance or 404 if no such object.
        """
        instance = None
        group_class = cls.classes[group_type]

        if group_class:
            instance = get_object_or_404(group_class, pk=group_id)

        # Implicitly returns BusinessUnit, or None if that is the type.
        # No need for an extra test.
        if group_class is MachineGroup:
            instance = instance.business_unit
        elif group_class is Machine:
            instance = instance.machine_group.business_unit

        return instance

    def get_group_instance(self):
        group_type = self.kwargs['group_type']
        group_id = self.kwargs['group_id']
        group_class = self.classes[group_type]
        if group_class:
            instance = get_object_or_404(group_class, pk=group_id)
        else:
            instance = None

        return instance

    def filter_queryset_by_group(self, queryset):
        """Filter queryset to only include group data.

        The filter depends on the request's group_type value. The
        provided queryset is filtered to include only records matching
        the view's specified BusinessUnit, MachineGroup, Machine (or
        not filtered at all for GA access).

        Args:
            queryset (Queryset): The queryset that should be filtered.

        Returns:
            Queryset with appropriate filter applied.
        """
        self.group_instance = self.get_group_instance()
        kwargs = {}
        # If our queryset model is Machine, and our group_type is
        # Machine, just filter to that machine and return. Deployed
        # doesn't factor in.
        if self.model is Machine and self.group_type == 'machine':
            kwargs['pk'] = self.group_id
        else:
            # Remove undeployed machines from the results.
            # It's important that we are filtering for deployed machines
            # here rather than excluding undeployed machines-you get
            # different results (exclude undeployed will exclude
            # Applications from list views that have ANY undeployed
            # machines.

            # This is a little wild, but it's either this or use an eval to
            # construct the keyword argument name to filter.
            deployed_filter = '{}{}deployed'.format(
                self.access_filter[queryset.model][Machine],
                '' if queryset.model is Machine else '__')
            kwargs[deployed_filter] = True
            # No need to filter if group_instance is None.
            if self.group_instance:
                filter_path = (
                    self.access_filter[queryset.model][self.classes[self.kwargs['group_type']]])
                kwargs[filter_path] = self.group_instance

        queryset = queryset.filter(**kwargs)

        return queryset


class DatatableQuerystringMixin():
    """Mixin to allow querystrings to work with DatatableViews

    Must come in a higher precedence spot in the MRO. (i.e. <<<---)
    """

    def get_datatable_kwargs(self, **kwargs):
        """Override DatatableView's func to allow querystrings."""
        # Currently this is only used by InventoryListView, but it may
        # prove useful elsewhere in the future, thus the Mixin vs.
        # just declaring it on the aforementioned view.
        kwargs = super(DatatableQuerystringMixin, self).get_datatable_kwargs(**kwargs)
        if hasattr(self, 'request'):
            kwargs['url'] = self.request.get_full_path
        return kwargs


class CSVResponseMixin():
    csv_filename = "sal_inventory"
    csv_ext = ".csv"
    components = []
    header = []

    def get_csv_filename(self):
        identifier = "_" + "_".join(self.components) if self.components else ""
        filename = "%s%s%s" % (self.csv_filename, identifier, self.csv_ext)
        return filename


class InventoryList(Datatable):

    # Specifying no source means we cannot sort on this column; however
    # the source value would be the total number of inventoryitem
    # records, NOT the number returned by the get_install_count
    # processor which filters by group_type. Without greatly increasing
    # the processing time for the view, we therefore cannot sort by
    # install count.
    install_count = DisplayColumn("Install Count", source=None, processor='get_install_count')

    class Meta:
        columns = ['hostname', 'serial', 'last_checkin', 'console_user', 'install_count']
        labels = {
            'hostname': 'Machine', 'serial': 'Serial Number', 'last_checkin': 'Last Checkin',
            'console_user': 'User'}
        processors = {'hostname': 'get_machine_link', 'last_checkin': 'format_date'}
        structure_template = 'datatableview/bootstrap_structure.html'
        page_length = server.utils.get_setting('datatable_page_length')

    def get_machine_link(self, instance, **kwargs):
        url = reverse("machine_detail", kwargs={"machine_id": instance.pk})

        return f'<a href="{url}">{instance.hostname}</a>'

    def get_install_count(self, instance, **kwargs):
        queryset = instance.inventoryitem_set.filter(application=kwargs['view'].application)
        field_type = kwargs['view'].field_type
        field_value = kwargs['view'].field_value
        if field_type == "path":
            queryset = queryset.filter(path=field_value)
        elif field_type == "version":
            queryset = queryset.filter(version=field_value)
        return queryset.count()

    def format_date(self, instance, **kwargs):
        return instance.last_checkin.strftime("%Y-%m-%d %H:%M:%S")


@class_login_required
@class_access_required
class InventoryListView(DatatableQuerystringMixin, DatatableView, GroupMixin):
    model = Machine
    template_name = "inventory/inventory_list.html"
    datatable_class = InventoryList
    csv_filename = "sal_inventory_list.csv"

    def get_queryset(self):
        # Save request values so we don't have to keep looking them up.
        self.group_type = self.kwargs.get("group_type", "all")
        self.group_id = self.kwargs.get("group_id", "0")
        self.field_type = self.request.GET.get("field_type", "all")
        self.field_value = self.request.GET.get("field_value", "")

        queryset = self.filter_queryset_by_group(self.model.objects.all())

        # Build a Q object to filter based on Application.
        self.application = get_object_or_404(Application, pk=self.kwargs["application_id"])
        application_q = Q(inventoryitem__application=self.application)

        # Build a Q object to filter based on the "field_type":
        # 'path' or 'version'
        kwargs = {}
        if self.field_type != "all":
            kwargs['inventoryitem__{}'.format(self.field_type)] = self.field_value
        field_q = Q(**kwargs)

        return queryset.filter(application_q, field_q).distinct()

    def get_context_data(self, **kwargs):
        context = super(InventoryListView, self).get_context_data(**kwargs)
        context["application_id"] = self.application.id
        context["group_type"] = self.group_type
        context["group_id"] = self.group_id
        # All of our models except Machine have a `name` attr. Machine
        # uses `hostname`. And the "all" group has none, so fail to
        # None.
        context["group_name"] = (
            self.group_instance.name if hasattr(self.group_instance, "name") else
            getattr(self.group_instance, 'hostname', None))
        context["app_name"] = self.application.name
        context["field_type"] = self.field_type
        context["field_value"] = self.field_value
        return context


class ApplicationList(Datatable):

    install_count = DisplayColumn(
        "Install Count", source='install_count', processor='get_install_count')

    class Meta:
        columns = ['name', 'bundleid', 'bundlename', 'install_count']
        labels = {'bundleid': 'Bundle ID', 'bundlename': 'Bundle Name'}
        processors = {'name': 'link_to_detail'}
        structure_template = 'datatableview/bootstrap_structure.html'
        page_length = server.utils.get_setting('datatable_page_length')

    def link_to_detail(self, instance, **kwargs):
        link_kwargs = copy.copy(kwargs['view'].kwargs)
        link_kwargs['pk'] = instance.pk
        url = reverse("application_detail", kwargs=link_kwargs)
        return f'<a href="{url}">{instance.name}</a>'

    def get_install_count(self, instance, **kwargs):
        """Get the number of app installs filtered by access group"""
        # Build a link to InventoryListView for install count badge.
        link_kwargs = copy.copy(kwargs['view'].kwargs)
        link_kwargs['application_id'] = instance.pk
        url = reverse("inventory_list", kwargs=link_kwargs)

        # Build the link.
        anchor = '<a href="{}"><span class="badge">{}</span></a>'.format(
            url, instance.install_count)
        return anchor


@class_login_required
@class_access_required
class ApplicationListView(DatatableView, GroupMixin):
    model = Application
    template_name = "inventory/application_list.html"
    datatable_class = ApplicationList

    def get_queryset(self):
        queryset = self.filter_queryset_by_group(self.model.objects).distinct()

        crufty_bundles = []

        # The inventory can be configured to filter bundleids out of
        # results by setting the 'inventory_exclusion_pattern' setting
        # in the SalSettings table.

        # The value of this setting should be a regular expression using
        # the python re module's syntax. You may delimit multiple
        # patterns with the '|' operator, e.g.:
        # 'com\.[aA]dobe.*|com\.apple\..*'
        if INVENTORY_PATTERN:
            crufty_bundles.append(INVENTORY_PATTERN)

        # By default, Sal will filter out the apps proxied through
        # VMWare and Parallels VMs. If you would like to disable this,
        # set the SalSetting 'filter_proxied_virtualization_apps' to
        # 'no' or 'false' (it's a string).
        if FILTER_VIRTUAL:
            # Virtualization proxied apps
            crufty_bundles.extend([r"com\.vmware\.proxyApp\..*", r"com\.parallels\.winapp\..*"])

        # Apple apps that are not generally used by users; currently
        # unused, but here for reference.
        # apple_cruft_pattern = (r'com.apple.(?!iPhoto)(?!iWork)(?!Aperture)'
        #     r'(?!iDVD)(?!garageband)(?!iMovieApp)(?!Server)(?!dt\.Xcode).*')

        crufty_pattern = '|'.join(crufty_bundles)
        if crufty_pattern:
            queryset = queryset.exclude(bundleid__regex=crufty_pattern)

        # Annotate the install counts in.
        return queryset.annotate(install_count=Count('inventoryitem'))

    def get_context_data(self, **kwargs):
        context = super(ApplicationListView, self).get_context_data(**kwargs)
        self.group_instance = self.get_group_instance()
        context["group_type"] = self.kwargs['group_type']
        if hasattr(self.group_instance, "name"):
            context["group_name"] = self.group_instance.name
        elif hasattr(self.group_instance, "hostname"):
            context["group_name"] = self.group_instance.hostname
        else:
            context["group_name"] = None
        context["group_id"] = self.group_instance.id if hasattr(self.group_instance, "id") else 0
        context["application_id"] = 0
        context["field_type"] = "all"
        context["field_value"] = 0
        return context


@class_login_required
@class_access_required
class ApplicationDetailView(DetailView, GroupMixin):
    model = Application
    template_name = "inventory/application_detail.html"

    def get_context_data(self, **kwargs):
        details = self._get_filtered_queryset()
        versions, paths = self._get_unique_items(details)
        context = super(ApplicationDetailView, self).get_context_data(**kwargs)
        return self._build_context_data(context, details, versions, paths)

    def _get_filtered_queryset(self):
        """Filter results based on URL parameters / user access."""
        return self.filter_queryset_by_group(self.object.inventoryitem_set)

    def _get_unique_items(self, details):
        """Use optimized DB methods for getting unique items if possible."""
        if server.utils.is_postgres():
            versions = (details
                        .order_by("version")
                        .distinct("version")
                        .values_list("version", flat=True))
            paths = details.order_by("path").distinct("path").values_list("path", flat=True)
        else:
            details = details.values()
            versions = {item["version"] for item in details}
            paths = {item["path"] for item in details}

            # We need to sort the versions for non-Postgres.
            versions = sorted(list(versions), key=lambda v: LooseVersion(v))

        return (versions, paths)

    def _build_context_data(self, context, details, versions, paths):
        # Get list of dicts of installed versions and number of installs
        # for each.
        context["versions"] = [
            {"version": version, "count": details.filter(version=version).count()} for version in
            versions]
        # Get list of dicts of installation locations and number of
        # installs for each.
        context["paths"] = [
            {"path": path, "count": details.filter(path=path).count()} for path in paths]
        # Get the total number of installations.
        context["install_count"] = details.count()
        # Add in access data.
        context["group_type"] = self.kwargs['group_type']
        context["group_id"] = self.kwargs['group_id']
        if hasattr(self.group_instance, "name"):
            group_name = self.group_instance.name
        elif hasattr(self.group_instance, "hostname"):
            group_name = self.group_instance.hostname
        else:
            group_name = None
        context["group_name"] = group_name

        return context


@class_login_required
@class_access_required
class CSVExportView(CSVResponseMixin, GroupMixin, View):
    model = InventoryItem

    def get(self, request, *args, **kwargs):
        # Filter data by access level
        queryset = self.filter_queryset_by_group(self.model.objects)

        # Group information is in the URL path
        group_type = self.kwargs['group_type']
        group_id = self.kwargs['group_id']

        # App id and filters are queries
        application_id = self.request.GET.get('pk', '0')
        field_type = self.request.GET.get('field_type', 'all')
        field_value = self.request.GET.get('field_value', '')

        if application_id == "0":
            # All Applications.
            self.components = ['application', 'list', 'for', group_type]
            if group_type != "all":
                self.components.append(group_id)

            fields = APPLICATION_FIELDS
            # The data we're retuurning is Applications, so get a
            # queryset of them to remove repetition of InventoryItems.
            applications = Application.objects.filter(pk__in=queryset.values('application__pk'))
            # Use the helper function to add attrs that wouldn't
            # normally be on this model (i.e. install count).
            data = (self.get_application_entry(item, queryset) for item in applications)

        else:
            # Inventory List for one application.
            application_name = get_object_or_404(Application, pk=application_id).name
            self.components = ["application", application_name, "for", group_type]
            if group_type != "all":
                self.components.append(group_id)
            if field_type != "all":
                self.components.extend(["where", field_type, "is", quote(field_value)])

            queryset = queryset.filter(application=application_id)
            if field_type == "path":
                queryset = queryset.filter(path=field_value)
            elif field_type == "version":
                queryset = queryset.filter(version=field_value)

            fields = utils.csv.machine_fields()
            data = (i.machine for i in queryset)

        return utils.csv.get_csv_response(data, fields, self.get_csv_filename())

    def get_application_entry(self, item, queryset):
        return ApplicationTuple(
            item.name,
            item.bundleid,
            item.bundlename,
            queryset.filter(application=item).count())


@csrf_exempt
@require_POST
@key_auth_required
def inventory_submit(request):
    # list of bundleids to ignore
    bundleid_ignorelist = ['com.apple.print.PrinterProxy']
    submission = request.POST
    serial = submission.get('serial').upper()
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            return HttpResponseNotFound('Serial Number not found')

        if 'base64bz2inventory' in submission:
            compressed_inventory = submission.get('base64bz2inventory')
            compression_type = 'base64bz2'
        elif 'base64inventory' in submission:
            compressed_inventory = submission.get('base64inventory')
            compression_type = 'base64'
        else:
            compressed_inventory = ''

        if compressed_inventory:
            compressed_inventory = compressed_inventory.replace(" ", "+")
            inventory_bytes = text_utils.decode_submission_data(
                compressed_inventory, compression_type)
            inventory_list = text_utils.submission_plist_loads(inventory_bytes)

            if inventory_list:
                try:
                    inventory_meta = Inventory.objects.get(machine=machine)
                except Inventory.DoesNotExist:
                    inventory_meta = Inventory(machine=machine)
                inventory_meta.sha256hash = hashlib.sha256(inventory_bytes).hexdigest()
                # clear existing inventoryitems
                machine.inventoryitem_set.all().delete()
                # insert current inventory items
                inventory_items_to_be_created = []
                for item in inventory_list:
                    app, _ = Application.objects.get_or_create(
                        bundleid=item.get("bundleid", ""),
                        name=item.get("name", ""),
                        bundlename=item.get("CFBundleName", ""))
                    # skip items in bundleid_ignorelist.
                    if not item.get('bundleid') in bundleid_ignorelist:
                        i_item = InventoryItem(
                            application=app,
                            version=item.get("version", ""),
                            path=item.get('path', ''),
                            machine=machine)
                        if server.utils.is_postgres():
                            inventory_items_to_be_created.append(i_item)
                        else:
                            i_item.save()
                machine.last_inventory_update = timezone.now()
                inventory_meta.save()

                if server.utils.is_postgres():
                    InventoryItem.objects.bulk_create(inventory_items_to_be_created)

            return HttpResponse("Inventory submitted for %s.\n" % submission.get('serial'))

    return HttpResponse("No inventory submitted.\n")


@csrf_exempt
@key_auth_required
def inventory_hash(request, serial):
    sha256hash = ""
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
            inventory_meta = Inventory.objects.get(machine=machine)
            sha256hash = inventory_meta.sha256hash
        except (Machine.DoesNotExist, Inventory.DoesNotExist):
            return HttpResponse("NOT FOUND")
    else:
        return HttpResponse("MACHINE NOT FOUND")
    return HttpResponse(sha256hash)
