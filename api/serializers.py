from django.forms import widgets
from rest_framework import serializers
from server.models import *

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
    facts = FactSerializer(many=True)
    conditions = ConditionSerializer(many=True)
    pending_apple_updates = PendingAppleUpdateSerializer(many=True)
    pending_updates = PendingUpdateSerializer(many=True)
    #machine_group = MachineGroupSerializer()
    class Meta:
        model = Machine
        exclude = ('id',)
