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
from search.views import *
from server.models import *


class MachineViewSet(viewsets.ModelViewSet):
    """
    list:
    Returns a paginated list of all machines in abbreviated form. Accepts
    querystring arguments for limiting fields.

    - `full` uses the full machine record instead of the abbreviated form.
        - Example: `/api/machines/?full`
    - `fields` allows you to specify a list of fields to include or exclude in
      the response.
        - Include Example: `/api/machines/?include=console_user,hostname`
        - Exclude Example: `/api/machines/?include!=report`
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer


class MachineInventory(generics.ListAPIView):
    """
    Retrieve machine inventory.
    """
    serializer_class = InventoryItemSerializer

    def get_queryset(self):
        """
        Get all of the inventory items for the machine
        """
        serial = self.kwargs['serial']
        return Machine.objects.get(serial=serial).inventoryitem_set.all()


class AllInventory(generics.ListAPIView):
    """
    Retrieve all the inventory items
    """
    serializer_class = InventoryItemSerializer
    queryset = InventoryItem.objects.all()


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


class FactsMachine(generics.ListAPIView):
    """
    Retrieve facts for a machine
    """
    serializer_class = FactSerializer
    def get_queryset(self):
        """
        Get all of the facts for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return Fact.objects.filter(machine=machine)


class Facts(generics.ListAPIView):
    """
    Retrieve a specific fact for all machines
    """
    serializer_class = FactWithSerialSerializer
    def get_queryset(self):
        fact_to_find = self.request.query_params.get('fact', None)
        if fact_to_find is not None:
            fact_to_find = fact_to_find.strip()

        return Fact.objects.filter(fact_name=fact_to_find)


class ConditionsMachine(generics.ListAPIView):
    """
    Retrieve conditions for a machine
    """
    serializer_class = ConditionSerializer
    def get_queryset(self):
        """
        Get all of the conditions for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return Condition.objects.filter(machine=machine)


class Conditions(generics.ListAPIView):
    """
    Retrieve a specific condition for all machines
    """
    serializer_class = ConditionWithSerialSerializer
    def get_queryset(self):
        condition_to_find = self.request.query_params.get('condition', None)
        if condition_to_find is not None:
            condition_to_find = condition_to_find.strip()

        return Condition.objects.filter(condition_name=condition_to_find)


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
