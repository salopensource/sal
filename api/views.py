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


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    filter_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename', 'machine__serial', 'version', 'path')
    search_fields = (
        'application__name', 'application__bundleid',
        'application__bundlename',)


class PendingAppleUpdates(generics.ListAPIView):
    """
    Retrieve pending apple updates for a machine.
    """
    serializer_class = PendingAppleUpdateSerializer
    def get_queryset(self):
        """
        Get all of the update items for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return PendingAppleUpdate.objects.filter(machine=machine)


class PendingUpdates(generics.ListAPIView):
    """
    Retrieve pending third party updates for a machine
    """
    serializer_class = PendingUpdateSerializer
    def get_queryset(self):
        """
        Get all of the update items for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return PendingUpdate.objects.filter(machine=machine)


class FactViewSet(FilterByMachineSerialMixin, viewsets.ReadOnlyModelViewSet):
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

    def get_queryset(self):
        queryset = super(FactViewSet, self).get_queryset()
        if 'serial' in self.request.query_params:
            machines = Machine.objects.filter(
                serial=self.request.query_params['serial'])
            queryset = queryset.filter(machine__in=machines)

        return queryset


class ConditionViewSet(FilterByMachineSerialMixin, viewsets.ReadOnlyModelViewSet):
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


class MachineGroupViewSet(viewsets.ModelViewSet):
    queryset = MachineGroup.objects.all()
    serializer_class = MachineGroupSerializer


class BusinessUnitViewSet(viewsets.ModelViewSet):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer


class PluginScriptSubmissionMachine(generics.ListAPIView):
    """
    Get the plugin script submissions for a machine
    """
    serializer_class = PluginScriptSubmissionSerializer
    def get_queryset(self):
        """
        Get all of the PluginScriptSubmissions for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return PluginScriptSubmission.objects.filter(machine=machine)


class PluginScriptSubmissionList(generics.ListAPIView):
    """
    List all plugin script submissions
    """
    queryset = PluginScriptSubmission.objects.all()
    serializer_class = PluginScriptSubmissionSerializer


class PluginScriptRowMachine(generics.ListAPIView):
    """
    Get the pluginscriptrows for a submission
    """
    queryset = PluginScriptRow.objects.all()
    lookup_field = 'pk'
    serializer_class = PluginScriptRowSerializer


class SearchID(generics.ListAPIView):
    """
    Retrieve a saved search
    """
    serializer_class = MachineSerializer
    def get_queryset(self):
        """
        Run the saved search
        """
        search_id = self.kwargs['pk']
        if search_id.endswith('/'):
            search_id = search_id[:-1]
        machines = Machine.objects.all()
        print search_machines(search_id, machines)
        return search_machines(search_id, machines, full=True)


class BasicSearch(generics.ListAPIView):
    """
    Perform a basic search
    """
    serializer_class = MachineSerializer
    def get_queryset(self):
        """
        Run the basic search
        """
        query = self.request.query_params.get('query', None)
        machines = Machine.objects.all()
        if query is not None:
            machines = quick_search(machines, query)

        return machines
# Retrieve all machines with a particular Fact value
