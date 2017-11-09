from django.forms import widgets

from rest_framework import serializers

from inventory.models import InventoryItem, Application
from mixins import QueryFieldsMixin
from server.models import *
from search.models import *


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

    submission = PluginScriptSubmissionSerializer()

    class Meta:
        model = PluginScriptRow
        fields = '__all__'


class FactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fact
        fields = '__all__'


class SerialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Machine
        fields = ('id','serial',)


class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        fields = '__all__'


class PendingAppleUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PendingAppleUpdate
        exclude = ('machine',)


class PendingUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PendingUpdate
        exclude = ('machine',)


class MachineSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    simple_fields = (
        'console_user', 'munki_version', 'hd_space', 'machine_model',
        'cpu_speed', 'serial', 'id', 'last_puppet_run', 'errors',
        'puppet_version', 'hostname', 'puppet_errors',
        'machine_model_friendly', 'memory', 'memory_kb', 'warnings',
        'first_checkin', 'last_checkin', 'hd_total', 'os_family', 'deployed',
        'operating_system', 'machine_group', 'sal_version', 'manifest',
        'hd_percent', 'cpu_type', 'activity')

    class Meta:
        model = Machine
        fields = '__all__'


class SavedSearchSerializer(serializers.ModelSerializer):

    class Meta:
        model = SavedSearch
        fields = '__all__'
