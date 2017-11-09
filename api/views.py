# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from django.http import Http404
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import *
from auth import *
from api.mixins import FilterByMachineSerialMixin
from search.views import *
from server.models import *


class BusinessUnitViewSet(viewsets.ModelViewSet):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer


class ConditionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Return conditions for all machines. Filter results by machine by including
    the querystring argument 'serial'.

    - Example: `/api/conditions/?serial=C0DEADBEEF00`

    retrieve:
    Return a condition by ID.
    """
    # TODO: The docstring above is to work around not showing the 'serial'
    # argument in the doc sites' "Query Parameters" table. Figure out how to do
    # this.

    queryset = Condition.objects.all()
    serializer_class = ConditionSerializer
    filter_fields = (
        'machine__serial', 'machine__hostname', 'condition_name',
        'condition_data')


class FactViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    Return facts for all machines. Filter results by machine by including the
    querystring argument 'serial'.

    - Example: `/api/facts/?serial=C0DEADBEEF00`

    retrieve:
    Return a fact by ID.
    """
    # TODO: The docstring above is to work around not showing the 'serial'
    # argument in the doc sites' "Query Parameters" table. Figure out how to do
    # this.
    queryset = Fact.objects.all()
    serializer_class = FactSerializer
    filter_fields = (
        'machine__serial', 'machine__hostname', 'fact_name',
        'fact_data')


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    filter_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename', 'machine__hostname', 'machine__serial',
        'version', 'path')
    search_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename',)


class MachineGroupViewSet(viewsets.ModelViewSet):
    queryset = MachineGroup.objects.all()
    serializer_class = MachineGroupSerializer


class MachineViewSet(viewsets.ModelViewSet):
    """
    list:
    Returns a paginated list of all machines. Records are by default in
    abbreviated form, but this endpoint accepts querystring arguments for
    limiting or including fields as per below.

    - `full` uses the full machine record instead of the abbreviated form.
        - Example: `/api/machines/?full`
    - `fields` allows you to specify a list of fields to include or exclude in
      the response.
        - Include Example: `/api/machines/?include=console_user,hostname`
        - Exclude Example: `/api/machines/?include!=report`

    The abbreviated form excludes the `report`, `install_log`, and
    `install_log_hash` fields.

    read:
    Returns a machine record. The returned record is by default in abbreviated
    form, but this endpoint accepts querystring arguments for limiting or
    including fields as per below.

    - `full` uses the full machine record instead of the abbreviated form.
        - Example: `/api/machines/42/?full`
    - `fields` allows you to specify a list of fields to include or exclude in
      the response.
        - Include Example: `/api/machines/C0DEADBEEF/?include=console_user,hostname`
        - Exclude Example: `/api/machines/C0DEADBEEF/?include!=report`

    The abbreviated form excludes the `report`, `install_log`, and
    `install_log_hash` fields.
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    lookup_field = 'serial'
    filter_fields = (
        'activity', 'console_user', 'cpu_speed', 'cpu_type', 'deployed',
        'errors', 'first_checkin', 'hd_percent', 'hd_space', 'hd_total',
        'hostname', 'last_checkin', 'last_puppet_run', 'machine_model',
        'machine_model_friendly', 'manifest', 'memory', 'memory_kb',
        'munki_version', 'operating_system', 'os_family', 'puppet_errors',
        'puppet_version', 'sal_version', 'warnings')
    search_fields = (
        'activity', 'console_user', 'cpu_speed', 'cpu_type', 'hostname',
        'machine_model', 'machine_model_friendly', 'manifest', 'memory')


class PendingAppleUpdatesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PendingAppleUpdateSerializer
    queryset = PendingAppleUpdate.objects.all()
    filter_fields = (
        'machine__serial', 'machine__hostname', 'update', 'update_version',
        'display_name')
    search_fields = ('display_name', 'update')


class PendingUpdatesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PendingUpdateSerializer
    queryset = PendingUpdate.objects.all()
    filter_fields = (
        'machine__serial', 'machine__hostname', 'update', 'update_version',
        'display_name')
    search_fields = ('display_name', 'update')


class PluginScriptRowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PluginScriptRow.objects.all()
    serializer_class = PluginScriptRowSerializer
    filter_fields = (
        'submission__machine__serial', 'submission__machine__hostname',
        'submission__plugin', 'pluginscript_name', 'pluginscript_data_string')


class SavedSearchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SavedSearch.objects.all()
    serializer_class = SavedSearchSerializer
