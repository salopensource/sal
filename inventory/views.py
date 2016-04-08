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
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
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


@class_login_required
@class_access_required
class InventoryListView(DatatableView, GroupMixin):
    model = InventoryItem
    template_name = "inventory/inventory_list.html"
    datatable_options = {
        'structure_template': 'datatableview/bootstrap_structure.html',
        'columns': [('Machine', 'machine'),
                    ("Serial Number", "machine__serial"),
                    ("Date", 'machine__last_checkin'),
                    ("User", "machine__console_user")]}

    def get_queryset(self):
        queryset = self.model.objects
        # Filter Application.objects based on type.
        # group_type = self.kwargs["group_type"]
        group_type = self.kwargs["group_type"]
        if group_type == "business_unit":
            business_unit = get_object_or_404(
                BusinessUnit, pk=self.kwargs["group_id"])
            queryset = queryset.filter(
                machine__machine_group__business_unit=business_unit)
        elif group_type == "machine_group":
            machine_group = get_object_or_404(
                MachineGroup, pk=self.kwargs["group_id"])
            queryset = queryset.filter(
                machine__machine_group=machine_group)
        elif group_type == "machine":
            machine = get_object_or_404(
                Machine, pk=self.kwargs["group_id"])
            queryset = queryset.filter(machine=machine)
        # Filter based on Applicagtion.
        self.application = get_object_or_404(
            Application, pk=self.kwargs["application_id"])
        queryset = queryset.filter(application=self.application)
        # Filter again based on criteria.
        field_type = self.kwargs["field_type"]
        if field_type == "path":
            queryset = queryset.filter(path=self.kwargs["field_value"])
        elif field_type == "version":
            queryset = queryset.filter(version=self.kwargs["field_value"])
        elif field_type == "all":
            pass
        else:
            raise Exception("TODO: Refine this.")

        # Return filtered Application.objects queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super(InventoryListView, self).get_context_data(**kwargs)
        context["app_name"] = self.application.name
        context["field_type"] = self.kwargs["field_type"]
        context["field_value"] = self.kwargs["field_value"]
        return context


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
            reverse("application-detail", kwargs=self.kwargs), instance.name)

    def get_install_count(self, instance, *args, **kwargs):
        inventory_items = instance.inventoryitem_set
        group_type = self.kwargs["group_type"]
        if group_type == "machine_group":
            machine_group = get_object_or_404(
                MachineGroup, pk=self.kwargs["group_id"])
            inventory_items = inventory_items.filter(
                machine__machine_group=machine_group)
        elif group_type == "business_unit":
            bu = get_object_or_404(
                BusinessUnit, pk=self.kwargs["group_id"])
            inventory_items = inventory_items.filter(
                machine__machine_group__business_unit=bu)
        elif group_type == "machine":
            machine = get_object_or_404(
                Machine, pk=self.kwargs["group_id"])
            inventory_items = inventory_items.filter(
                machine=machine)

        # TODO: Does this sometimes leave a group_type of ""/None?
        url_kwargs = {"group_type": group_type,
                      "group_id": (0 if group_type == "all" else
                                   self.kwargs["group_id"]),
                      "application_id": instance.pk,
                      "field_type": "all",
                      "field_value": 0}
        return ('<a href="%s"><span class="badge">%s</span></a>' %
                (reverse("inventory_list", kwargs=url_kwargs),
                 inventory_items.count()))


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
        group_type = self.kwargs["group_type"]
        group_class = self.classes[group_type]
        if group_class:
            group_object = get_object_or_404(
                group_class, pk=self.kwargs["group_id"])
        if group_class is MachineGroup:
            details = self.object.inventoryitem_set.values(
                "version", "path", "machine").filter(
                    machine__machine_group=group_object)
        elif group_class is BusinessUnit:
            details = self.object.inventoryitem_set.values(
                "version", "path", "machine").filter(
                    machine__machine_group__business_unit=group_object)
        elif group_class is Machine:
            details = self.object.inventoryitem_set.values(
                "version", "path", "machine").filter(machine=group_object)
        else:
            details = self.object.inventoryitem_set.values("version", "path")

        return details

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

        return context


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


# TODO: Refactor! (New models as well)
@login_required
def export_csv(request, page='front', theID=None):
    user = request.user
    title = 'Inventory Export'
    inventory_name = request.GET.get('name')
    inventory_version = request.GET.get('version', '0')
    inventory_bundleid = request.GET.get('bundleid', '')
    inventory_path = request.GET.get('path')
    inventory_bundlename = request.GET.get('bundlename', '')
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(
            business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines_unsorted = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines_unsorted = (machines_unsorted |
                                     machine_group.machine_set.all())
        else:
            machines_unsorted = None
        machines = machines_unsorted

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)

    if page == 'machine_id':
        machines = Machine.objects.filter(id=theID)

    # get the InventoryItems limited to the machines we're allowed to look at
    inventoryitems = InventoryItem.objects.filter(
        name=inventory_name, version=inventory_version,
        bundleid=inventory_bundleid,
        bundlename=inventory_bundlename).filter(machine=machines).order_by(
            'name')

    machines = machines.filter(inventoryitem__name=inventory_name,
                               inventoryitem__version=inventory_version,
                               inventoryitem__bundleid=inventory_bundleid,
                               inventoryitem__bundlename=inventory_bundlename)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title

    writer = csv.writer(response)
    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if (not field.is_relation and
                field.name != 'id' and
                field.name != 'report' and
                field.name != 'activity' and
                field.name != 'os_family'):
            header_row.append(field.name)
    header_row.append('business_unit')
    header_row.append('machine_group')
    writer.writerow(header_row)
    for machine in machines:
        row = []
        for name, value in machine.get_fields():
            if (name != 'id' and
                    name != 'machine_group' and
                    name != 'report' and
                    name != 'activity' and
                    name != 'os_family'):
                row.append(value.strip())
        row.append(machine.machine_group.business_unit.name)
        row.append(machine.machine_group.name)
        writer.writerow(row)
        # writer.writerow([machine.serial,
        #                  machine.machine_group.business_unit.name,
        #                  machine.machine_group.name, machine.hostname,
        #                  machine.operating_system, machine.memory,
        #                  machine.memory_kb, machine.munki_version,
        #                  machine.manifest])

    return response


@login_required
def inventory_list(request, page='front', theID=None):
    user = request.user
    title = None
    inventory_name = request.GET.get('name')
    inventory_version = request.GET.get('version', '0')
    inventory_bundleid = request.GET.get('bundleid', '')
    # Unused
    # inventory_path = request.GET.get('path')
    inventory_bundlename = request.GET.get('bundlename', '')

    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this

        machines = utils.getBUmachines(theID)

    if page == 'group_dashboard' or page == 'machine_group':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)

    if page == 'machine_id':
        machines = Machine.objects.filter(id=theID)

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25

    # get the InventoryItems limited to the machines we're allowed to look at
    inventory = InventoryItem.objects.filter(
        name=inventory_name, version=inventory_version,
        bundleid=inventory_bundleid,
        bundlename=inventory_bundlename).filter(machine=machines)[start:end]

    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0

    c = {'user':user, 'machines': machines, 'req_type': page, 'title':
         title, 'bu_id': theID, 'request':request,
         'inventory_name':inventory_name,
         'inventory_version':inventory_version,
         'inventory_bundleid':inventory_bundleid,
         'inventory_bundlename':inventory_bundlename, 'previous_id':
         previous_id, 'next_id':next_id, 'inventory':inventory}

    return render_to_response('inventory/overview_list_all.html', c,
                              context_instance=RequestContext(request))
