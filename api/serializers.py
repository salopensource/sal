from django.forms import widgets

from rest_framework import serializers

from inventory.models import InventoryItem, Application
from server.models import *


class InventoryApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = '__all__'


class InventoryItemSerializer(serializers.ModelSerializer):
    application = InventoryApplicationSerializer()

    class Meta:
        model = InventoryItem
        fields = '__all__'


class BusinessUnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessUnit
        fields = '__all__'


class MachineGroupSerializer(serializers.ModelSerializer):
    business_unit = serializers.PrimaryKeyRelatedField(
        queryset=BusinessUnit.objects.all())

    class Meta:
        model = MachineGroup
        fields = '__all__'


class PluginScriptSubmissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PluginScriptSubmission
        fields = '__all__'


class PluginScriptRowSerializer(serializers.ModelSerializer):

    class Meta:
        model = PluginScriptRow
        fields = '__all__'


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
    facts = FactSerializer(many=True, required=False)
    conditions = ConditionSerializer(many=True, required=False)
    pending_apple_updates = PendingAppleUpdateSerializer(
        many=True, required=False)
    pending_updates = PendingUpdateSerializer(many=True, required=False)

    class Meta:
        model = Machine
        fields = '__all__'


class MachineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Machine
        exclude = ('report','install_log','install_log_hash')
