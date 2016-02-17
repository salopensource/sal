from django.forms import widgets
from rest_framework import serializers
from inventory.models import InventoryItem
from server.models import *

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        exclude = ('machine',)

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
        exclude = ('machine',)

class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        exclude = ('machine',)


class PendingAppleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingAppleUpdate
        exclude = ('machine',)

class PendingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpdate
        exclude = ('machine',)

class MachineSerializer(serializers.ModelSerializer):
    facts = FactSerializer(many=True, required=False)
    conditions = ConditionSerializer(many=True, required=False)
    pending_apple_updates = PendingAppleUpdateSerializer(many=True, required=False)
    pending_updates = PendingUpdateSerializer(many=True, required=False)

    class Meta:
        model = Machine
