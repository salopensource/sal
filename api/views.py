# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from server.models import *
from api.serializers import *
from auth import *
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

class PendingAppleUpdates(generics.ListAPIView):
    """
    Retrieve pending apple updates for a machine.
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
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
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    serializer_class = PendingUpdateSerializer
    def get_queryset(self):
        """
        Get all of the update items for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return PendingUpdate.objects.filter(machine=machine)

class Facts(generics.ListAPIView):
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


class Conditions(generics.ListAPIView):
    """
    Retrieve conditions for a machine
    """
    authentication_classes = (ApiKeyAuthentication,)
    permission_classes = (HasRWPermission,)
    serializer_class = ConditionSerializer
    def get_queryset(self):
        """
        Get all of the conditions for the machine
        """
        serial = self.kwargs['serial']
        machine = Machine.objects.get(serial=serial)
        return Condition.objects.filter(machine=machine)

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

# Retrieve all machines with a particular Fact value
