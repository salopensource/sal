# standard library
import hashlib
import plistlib
from datetime import datetime

# third-party
import unicodecsv as csv

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, View
from datatableview.views import DatatableView

# local Django
from models import Application, Inventory, InventoryItem
from server import utils
from sal.decorators import class_login_required, class_access_required
from server.models import BusinessUnit, MachineGroup, Machine


class GroupMixin(object):
    """Mixin to add get_business_unit method for access decorators."""
    classes = {"all": None,
               "business_unit": BusinessUnit,
               "machine": Machine,
               "machine_group": MachineGroup}

    @classmethod
    def get_business_unit(cls, **kwargs):
        instance = None
        group_class = cls.classes[kwargs["group_type"]]

        if group_class:
            instance = get_object_or_404(
                group_class, pk=kwargs["group_id"])

        # Implicitly returns BusinessUnit, or None if that is the type.
        # No need for an extra test.
        if group_class is MachineGroup:
            instance = instance.business_unit
        elif group_class is Machine:
            instance = instance.machine_group.business_unit

        return instance

    def get_group_instance(self):
        group_type = self.kwargs["group_type"]
        group_class = self.classes[group_type]
        if group_class:
            instance = get_object_or_404(
                group_class, pk=self.kwargs["group_id"])
        else:
            instance = None

        return instance

    def filter_inventoryitem_by_group(self, queryset):
        if isinstance(self.group_instance, BusinessUnit):
            queryset = queryset.filter(
                machine__machine_group__business_unit=self.group_instance)
        elif isinstance(self.group_instance, MachineGroup):
            queryset = queryset.filter(
                machine__machine_group=self.group_instance)
        elif isinstance(self.group_instance, Machine):
            queryset = queryset.filter(machine=self.group_instance)

        return queryset


class CSVResponseMixin(object):
    csv_filename = 'sal_inventory.csv'

    def get_csv_filename(self):
        return self.csv_filename

    def set_header(self, headers):
        self._header = headers

    def render_to_csv(self, data):
        response = HttpResponse(content_type='text/csv')
        cd = 'attachment; filename="{0}"'.format(self.get_csv_filename())
        response['Content-Disposition'] = cd

        writer = csv.writer(response)
        if hasattr(self, "_header"):
            writer.writerow(self._header)
        for row in data:
            writer.writerow(row)

        return response


@class_login_required
@class_access_required
class InventoryListView(DatatableView, GroupMixin):
    model = InventoryItem
    template_name = "inventory/inventory_list.html"
    datatable_options = {
        'structure_template': 'datatableview/bootstrap_structure.html',
        'columns': [('Machine', 'machine'),
                    ("Serial Number", "machine__serial"),
                    ("Date", 'machine__last_checkin', 'format_date'),
                    ("User", "machine__console_user")]}

    def get_queryset(self):
        self.group_instance = self.get_group_instance()
        queryset = self.model.objects
        queryset = self.filter_inventoryitem_by_group(queryset)

        # Filter based on Application.
        self.application = get_object_or_404(
            Application, pk=self.kwargs["application_id"])
        queryset = queryset.filter(application=self.application)

        # Filter again based on criteria.
        field_type = self.kwargs["field_type"]
        if field_type == "path":
            queryset = queryset.filter(path=self.kwargs["field_value"])
        elif field_type == "version":
            queryset = queryset.filter(version=self.kwargs["field_value"])

        return queryset

    def get_context_data(self, **kwargs):
        context = super(InventoryListView, self).get_context_data(**kwargs)
        context["application_id"] = self.application.id
        context["group_type"] = self.kwargs["group_type"]
        context["group_id"] = self.kwargs["group_id"]
        context["group_name"] = (self.group_instance.name if hasattr(
            self.group_instance, "name") else None)
        context["app_name"] = self.application.name
        context["field_type"] = self.kwargs["field_type"]
        context["field_value"] = self.kwargs["field_value"]
        return context

    def format_date(self, instance, *args, **kwargs):
        return instance.machine.last_checkin.strftime("%Y-%m-%d %H:%M:%S")


@class_login_required
@class_access_required
class ApplicationListView(DatatableView, GroupMixin):
    model = Application
    template_name = "inventory/application_list.html"
    datatable_options = {
        'structure_template': 'datatableview/bootstrap_structure.html',
        'columns': [('Name', 'name', "get_name_link"),
                    ("Bundle ID", 'bundleid'),
                    ("Bundle Name", 'bundlename'),
                    ("Install Count", None, "get_install_count")]}

    def get_name_link(self, instance, *args, **kwargs):
        params = self.kwargs
        params["pk"] = instance.pk
        return '<a href="%s">%s</a>' % (
            reverse("application_detail", kwargs=self.kwargs), instance.name)

    def get_install_count(self, instance, *args, **kwargs):
        self.group_instance = self.get_group_instance()
        queryset = instance.inventoryitem_set
        queryset = self.filter_inventoryitem_by_group(queryset)

        # Build a link to InventoryListView for install count badge.
        url_kwargs = {
            "group_type": self.kwargs["group_type"],
            "group_id": self.kwargs["group_id"],
            "application_id": instance.pk,
            "field_type": "all",
            "field_value": 0}
        url = reverse("inventory_list", kwargs=url_kwargs)
        anchor = '<a href="%s"><span class="badge">%s</span></a>' % (
            url, queryset.count())
        # import pdb;pdb.set_trace()
        return anchor

    def get_context_data(self, **kwargs):
        context = super(ApplicationListView, self).get_context_data(**kwargs)
        self.group_instance = self.get_group_instance()
        context["group_type"] = self.kwargs["group_type"]
        if hasattr(self.group_instance, "name"):
            context["group_name"] = self.group_instance.name
        elif hasattr(self.group_instance, "hostname"):
            context["group_name"] = self.group_instance.hostname
        else:
            context["group_name"] = None
        context["group_id"] = (self.group_instance.id if hasattr(
            self.group_instance, "id") else 0)
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
        self.group_instance = self.get_group_instance()
        queryset = self.object.inventoryitem_set
        # TODO: Remove unnecessary values call
        queryset = self.filter_inventoryitem_by_group(queryset).values()
        return queryset

    def _get_unique_items(self, details):
        """Use optimized DB methods for getting unique items if possible."""
        if is_postgres():
            versions = self.object.inventoryitem_set.distinct("version")
            paths = self.object.inventoryitem_set.distinct("path")
        else:
            versions = {item["version"] for item in details}
            paths = {item["path"] for item in details}

        return (versions, paths)

    def _build_context_data(self, context, details, versions, paths):
        # Get list of dicts of installed versions and number of installs
        # for each.
        context["versions"] = [
            {"version": version,
             "count": details.filter(version=version).count()} for
            version in versions]
        # Get list of dicts of installation locations and number of
        # installs for each.
        context["paths"] = [
            {"path": path, "count": details.filter(path=path).count()}
            for path in paths]
        # Get the total number of installations.
        context["install_count"] = details.count()
        # Add in access data.
        context["group_type"] = self.kwargs["group_type"]
        context["group_id"] = self.kwargs["group_id"]
        context["group_name"] = (self.group_instance.name if hasattr(
            self.group_instance, "name") else None)
        # TODO: Add in field_type/field_value for export link to reverse.
        # context["field_type"] = "all"
        # context["field_value"] = 0

        return context


@class_login_required
@class_access_required
class CSVExportView(CSVResponseMixin, GroupMixin, View):
    model = InventoryItem

    def get(self, rqeuest, *args, **kwargs):
        # Filter data by access level
        self.group_instance = self.get_group_instance()
        queryset = self.model.objects
        queryset = self.filter_inventoryitem_by_group(queryset)

        # TODO: Add in report name.

        if kwargs["application_id"] == "0":
            # TODO: Not tested.
            if is_postgres():
                apps = [[item.application.name,
                        item.application.bundleid,
                        item.application.bundlename,
                        queryset.filter(application=item.application).count()]
                        for item in
                        queryset.select_related("application").distinct(
                            "application")]
            else:
                # We build a set of tuples, as mutable types are not hashable.
                apps = {(item.application.name,
                        item.application.bundleid,
                        item.application.bundlename,
                        queryset.filter(application=item.application).count())
                        for item in queryset.select_related("application")}

            data = sorted(apps, key=lambda x: x[0])
            self.set_header(["Name", "BundleID", "BundleName",
                             "Install Count"])
        else:
            # Inventory List for one application.
            queryset = queryset.filter(application=kwargs["application_id"])
            if kwargs["field_type"] == "path":
                queryset = queryset.filter(
                    path=kwargs["field_value"])
            elif kwargs["field_type"] == "version":
                queryset = queryset.filter(
                    version=kwargs["field_value"])

            data = [[item.machine.hostname,
                    item.machine.serial,
                    item.machine.last_checkin,
                    item.machine.console_user] for
                    item in queryset.select_related("machine")]
            self.set_header(["Hostname", "Serial Number", "Last Checkin",
                             "Console User"])

        return self.render_to_csv(data)


@csrf_exempt
def inventory_submit(request):
    if request.method != 'POST':
        return HttpResponseNotFound('No POST data sent')

    # list of bundleids to ignore
    bundleid_ignorelist = [
        'com.apple.print.PrinterProxy'
    ]
    submission = request.POST
    serial = submission.get('serial')
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            return HttpResponseNotFound('Serial Number not found')

        compressed_inventory = submission.get('base64bz2inventory')
        if compressed_inventory:
            compressed_inventory = compressed_inventory.replace(" ", "+")
            inventory_str = utils.decode_to_string(compressed_inventory)
            try:
                inventory_list = plistlib.readPlistFromString(inventory_str)
            except Exception:
                inventory_list = None
            if inventory_list:
                try:
                    inventory_meta = Inventory.objects.get(machine=machine)
                except Inventory.DoesNotExist:
                    inventory_meta = Inventory(machine=machine)
                inventory_meta.sha256hash = \
                    hashlib.sha256(inventory_str).hexdigest()
                # clear existing inventoryitems
                machine.inventoryitem_set.all().delete()
                # insert current inventory items
                for item in inventory_list:
                    app, _ = Application.objects.get_or_create(
                        bundleid=item.get("bundleid", ""),
                        name=item.get("name", ""),
                        bundlename=item.get("CFBundleName", ""))
                    print app.name
                    # skip items in bundleid_ignorelist.
                    if not item.get('bundleid') in bundleid_ignorelist:
                        i_item = machine.inventoryitem_set.create(
                            application=app, version=item.get("version", ""),
                            path=item.get('path', ''))
                machine.last_inventory_update = datetime.now()
                inventory_meta.save()
            machine.save()
            return HttpResponse(
                "Inventory submmitted for %s.\n" %
                submission.get('serial'))

    return HttpResponse("No inventory submitted.\n")


def is_postgres():
    postgres_backend = 'django.db.backends.postgresql_psycopg2'
    db_setting = settings.DATABASES['default']['ENGINE']
    return db_setting == postgres_backend


@csrf_exempt
def inventory_hash(request, serial):
    sha256hash = ""
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
            inventory_meta = Inventory.objects.get(machine=machine)
            sha256hash = inventory_meta.sha256hash
        except (Machine.DoesNotExist, Inventory.DoesNotExist):
            pass
    else:
        return HttpResponse("MACHINE NOT FOUND")
    return HttpResponse(sha256hash)


