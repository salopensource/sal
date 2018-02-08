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
        fields = ('id', 'serial',)


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
        'hd_percent', 'cpu_type', 'broken_client', 'report_format')

    class Meta:
        model = Machine
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """Modify the serializer's fields if the full argument is true.

        This is taken from the DRF Serializers: Dynamically Modifying
        Fields example to allow us to handle one case: during our
        conversion of the Queryset result of the Search module's
        search_machine method into json for API usage in the
        /api/saved_search/<id>/execute endpoint (which by default does
        not return the full results). This causes the serializer to
        freak out because there are not fields to serialize.
        """
        # There's probably a better way to do this.

        # Pop off special kwargs so they don't mess up the parent init.
        full_query = kwargs.pop('full', None)
        saved_search = kwargs.pop('saved_search', None)

        super(MachineSerializer, self).__init__(*args, **kwargs)

        # Only used by saved_search
        if saved_search and not full_query:
            # See sal/search/views.py for the source of the included
            # fields.
            allowed = {'id', 'serial', 'console_user', 'hostname', 'last_checkin'}
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class SearchRowSerializer(serializers.ModelSerializer):

    class Meta:
        model = SearchRow
        fields = '__all__'


class SearchGroupSerializer(serializers.ModelSerializer):
    search_rows = SearchRowSerializer(source='searchrow_set', read_only=True, many=True)

    class Meta:
        model = SearchGroup
        fields = '__all__'


class SavedSearchSerializer(serializers.ModelSerializer):
    search_groups = SearchGroupSerializer(source='searchgroup_set', read_only=True, many=True)

    class Meta:
        model = SavedSearch
        fields = '__all__'
