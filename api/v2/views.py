from django.http import Http404
from rest_framework.decorators import detail_route
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *
from api.auth import *
from .mixins import QueryFieldsMixin
from search.views import *
from server.models import *
from profiles.models import *


class BusinessUnitViewSet(viewsets.ModelViewSet):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer
    filter_fields = ('name',)


class FactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fact.objects.all()
    serializer_class = FactSerializer
    filter_fields = (
        'machine__serial', 'machine__hostname', 'machine__id',
        'fact_name', 'fact_data')


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    You may also use the `search` querystring to perform text searches
    across the `application__name`, `application__bundleid`,
        `application__bundlename` fields.

    Example `/api/inventory/?search=Adobe`
    """
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    filter_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename', 'machine__hostname', 'machine__serial',
        'machine__id', 'version', 'path')
    search_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename',)


class MachineGroupViewSet(viewsets.ModelViewSet):
    queryset = MachineGroup.objects.all()
    serializer_class = MachineGroupSerializer
    filter_fields = ('name', 'business_unit__name', 'business_unit__id')


class MachineViewSet(QueryFieldsMixin, viewsets.ModelViewSet):
    """
    list:
    Returns a paginated list of all machines. Records are by default in
    abbreviated form, but this endpoint accepts querystring arguments for
    limiting or including fields as per below.

    - `full` uses the full machine record instead of the abbreviated form.
        - Example: `/api/machines/?full`
    - `fields` allows you to specify a list of fields to include or exclude in
      the response.
        - Include Example: `/api/machines/?fields=console_user,hostname`
        - Exclude Example: `/api/machines/?fields!=report`

    The abbreviated form excludes the `report` field.

    You may also use the `search` querystring to perform text searches
    across the `console_user`, `cpu_speed`, `cpu_type`,
    `hostname`, `machine_model`, `machine_model_friendly`, `manifest`,
    and `memory` fields.

    Example `/api/machines/?search=MacPro`

    read:
    Returns a machine record. The returned record is by default in abbreviated
    form, but this endpoint accepts querystring arguments for limiting or
    including fields as per below.

    - `full` uses the full machine record instead of the abbreviated form.
        - Example: `/api/machines/42/?full`
    - `fields` allows you to specify a list of fields to include or exclude in
      the response.
        - Include Example: `/api/machines/C0DEADBEEF/?fields=console_user,hostname`
        - Exclude Example: `/api/machines/C0DEADBEEF/?fields!=report`

    The abbreviated form excludes the `report` field.
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    lookup_field = 'serial'
    filter_fields = (
        'id', 'activity', 'console_user', 'cpu_speed', 'cpu_type', 'deployed',
        'errors', 'first_checkin', 'hd_percent', 'hd_space', 'hd_total',
        'hostname', 'last_checkin', 'last_puppet_run', 'machine_model',
        'machine_model_friendly', 'manifest', 'memory', 'memory_kb',
        'munki_version', 'operating_system', 'os_family', 'puppet_errors',
        'puppet_version', 'sal_version', 'warnings')
    search_fields = (
        'console_user', 'cpu_speed', 'cpu_type', 'hostname',
        'machine_model', 'machine_model_friendly', 'manifest', 'memory')


class UpdateHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:
    You may also use the `search` querystring to perform text searches
    across the `name` and `version` fields.

    Example `/api/update_history/?search=NetHack`
    """
    serializer_class = UpdateHistorySerializer
    queryset = UpdateHistory.objects.all()
    filter_fields = (
        'machine__serial', 'machine__hostname', 'machine__id',
        'update_type', 'name', 'version')
    search_fields = ('name', 'version')


class ManagementSourceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ManagementSourceSerializer
    queryset = ManagementSource.objects.all()


class ManagedItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ManagedItemSerializer
    queryset = ManagedItem.objects.all()
    filter_fields = (
        'machine__serial', 'machine__hostname', 'machine__id',
        'management_source__name', 'management_source__id', 'status')
    search_fields = ('name', )


class PluginScriptRowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PluginScriptRow.objects.all()
    serializer_class = PluginScriptRowSerializer
    filter_fields = (
        'submission__machine__serial', 'submission__machine__hostname',
        'submission__plugin', 'pluginscript_name', 'pluginscript_data_string')


class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    filter_fields = (
        'machine__serial', 'machine__hostname', 'machine__id',
        'identifier', 'uuid')
    search_fields = ('identifier', 'uuid')


class SavedSearchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    execute:
    This endpoint will execute the `SavedSearch`specified by the passed
    ID number, and return the resulting list of `Machines`.

    You may add `?full` to the end of the URL to specify that you would
    like the full `Machine` record rather than just the `id`, `serial`,
    `console_user` and  `last_checkin` values.

    For example, `/api/saved_searches/666/execute`
    """
    queryset = SavedSearch.objects.all()
    serializer_class = SavedSearchSerializer

    @detail_route()
    def execute(self, request, pk=None):
        machines = Machine.objects.all()
        try:
            query_params = request.query_params
        except AttributeError:
            # DRF 2
            query_params = getattr(request, 'QUERY_PARAMS', request.GET)

        full = True if 'full' in query_params else False
        queryset = search_machines(pk, machines, full=full)
        # Pass the "full" parameter to the serializer so it knows
        # how to handle potentially missing fields.
        response_data = MachineSerializer(
            queryset, many=True, full=full, saved_search=True)
        return Response(response_data.data)
