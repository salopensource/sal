from django.forms import widgets
from rest_framework import serializers
from inventory.models import InventoryItem
from server.models import *

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        exclude = ('id', 'machine')

class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit

class MachineGroupSerializer(serializers.ModelSerializer):
    #business_unit = BusinessUnitSerializer()
    class Meta:
        model = MachineGroup

class FactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fact
        exclude = ('id', 'machine')

class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        exclude = ('id', 'machine')


class PendingAppleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingAppleUpdate
        exclude = ('id', 'machine')

class PendingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpdate
        exclude = ('id', 'machine')

class MachineSerializer(serializers.ModelSerializer):
    facts = FactSerializer(many=True, required=False)
    conditions = ConditionSerializer(many=True, required=False)
    pending_apple_updates = PendingAppleUpdateSerializer(many=True, required=False)
    pending_updates = PendingUpdateSerializer(many=True, required=False)
    #machine_group = MachineGroupSerializer()
    class Meta:
        model = Machine
        exclude = ('id',)
