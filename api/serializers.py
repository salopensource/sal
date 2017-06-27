from django.forms import widgets
from rest_framework import serializers
from inventory.models import InventoryItem
from server.models import *

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        # exclude = ('machine',)

class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit

class MachineGroupSerializer(serializers.ModelSerializer):
    #business_unit = BusinessUnitSerializer()
    class Meta:
        model = MachineGroup

class PluginScriptSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginScriptSubmission

class PluginScriptRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = PluginScriptRow

class FactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fact
        exclude = ('machine',)

class SerialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ('id','serial',)


class FactWithSerialSerializer(serializers.ModelSerializer):
    machine = SerialSerializer()
    class Meta:
        model = Fact

class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        exclude = ('machine',)

class ConditionWithSerialSerializer(serializers.ModelSerializer):
    # serial = serializers.CharField()
    machine = SerialSerializer()
    class Meta:
        model = Condition

class PendingAppleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingAppleUpdate
        exclude = ('machine',)

class PendingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUpdate
        exclude = ('machine',)

class FullMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine

class MachineSerializer(serializers.ModelSerializer):
    # facts = FactSerializer(many=True, required=False)
    # conditions = ConditionSerializer(many=True, required=False)
    # pending_apple_updates = PendingAppleUpdateSerializer(many=True, required=False)
    # pending_updates = PendingUpdateSerializer(many=True, required=False)

    class Meta:
        model = Machine
        exclude = ('report','install_log','install_log_hash')
