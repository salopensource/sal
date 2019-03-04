from server.models import *
from api.v1.serializers import *
from api.auth import *
from search.views import *
from django.http import Http404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination


class MachineList(generics.ListCreateAPIView):
    """
    List all machines, or create a new machine.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer


class MachineListFullDetail(generics.ListCreateAPIView):
    """
    List all machines in full details, or create a new machine.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = Machine.objects.all()
    serializer_class = FullMachineSerializer


class MachineDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a machine.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = Machine.objects.all()
    lookup_field = 'serial'
    serializer_class = MachineSerializer


class MachineFullDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve full details, update or delete a machine.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = Machine.objects.all()
    lookup_field = 'serial'
    serializer_class = FullMachineSerializer


class MachineInventory(generics.ListAPIView):
    """
    Retrieve machine inventory.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
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
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    serializer_class = InventoryItemSerializer
    queryset = InventoryItem.objects.all()


class FactsMachine(generics.ListAPIView):
    """
    Retrieve facts for a machine
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
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
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    serializer_class = FactWithSerialSerializer

    def get_queryset(self):
        fact_to_find = self.request.query_params.get('fact', None)
        if fact_to_find is not None:
            fact_to_find = fact_to_find.strip()

        return Fact.objects.filter(fact_name=fact_to_find)


class MachineGroupView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve details, update or remove a machine group
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = MachineGroup.objects.all()
    lookup_field = 'pk'
    serializer_class = MachineGroupSerializer


class MachineGroupList(generics.ListCreateAPIView):
    """
    List all machine groups, or create a new machine group.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = MachineGroup.objects.all()
    lookup_field = 'pk'
    serializer_class = MachineGroupSerializer


class BusinessUnitView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve details, update or remove a business unit
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = BusinessUnit.objects.all()
    lookup_field = 'pk'
    serializer_class = BusinessUnitSerializer


class BusinessUnitList(generics.ListCreateAPIView):
    """
    List all machine groups, or create a new business unit
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = BusinessUnit.objects.all()
    lookup_field = 'pk'
    serializer_class = BusinessUnitSerializer


class PluginScriptSubmissionMachine(generics.ListAPIView):
    """
    Get the plugin script submissions for a machine
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
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
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = PluginScriptSubmission.objects.all()
    serializer_class = PluginScriptSubmissionSerializer


class PluginScriptRowMachine(generics.ListAPIView):
    """
    Get the pluginscriptrows for a submission
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    queryset = PluginScriptRow.objects.all()
    lookup_field = 'pk'
    serializer_class = PluginScriptRowSerializer


class SearchID(generics.ListAPIView):
    """
    Retrieve a saved search
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    serializer_class = MachineSerializer

    def get_queryset(self):
        """
        Run the saved search
        """
        search_id = self.kwargs['pk']
        if search_id.endswith('/'):
            search_id = search_id[:-1]
        machines = Machine.objects.all()
        return search_machines(search_id, machines, full=True)


class BasicSearch(generics.ListAPIView):
    """
    Perform a basic search
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
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
