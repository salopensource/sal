from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from server.models import *
from api.serializers import *
from auth import *
from json_response import *

@csrf_exempt
@validate_api_key
def machine_list(request):
    """
    List all machines, or create a new machine.
    """
    if request.method == 'GET':
        machines = Machine.objects.all()
        serializer = MachineSerializer(machines, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MachineSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)

@csrf_exempt
@validate_api_key
def machine_detail(request, serial):
    """
    Retrieve, update or delete a machine.
    """
    try:
        machine = Machine.objects.get(serial=serial)
    except Machine.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = MachineSerializer(machine)
        return JSONResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = MachineSerializer(machine, data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data)
        return JSONResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        machine.delete()
        return HttpResponse(status=204)

@validate_api_key
@csrf_exempt
def facts(request, serial):
    """
    Retrieves facts for a given machine.
    """
    try:
        machine = Machine.objects.get(serial=serial)
    except Machine.DoesNotExist:
        return HttpResponse(status=404)

    facts = Fact.objects.filter(machine=machine)
    if request.method == 'GET':
        serializer = FactSerializer(facts, many=True)
        return JSONResponse(serializer.data)


@validate_api_key
@csrf_exempt
def conditions(request, serial):
    """
    Retrieves conditions for a given machine.
    """
    try:
        machine = Machine.objects.get(serial=serial)
    except Machine.DoesNotExist:
        return HttpResponse(status=404)

    conditions = Condition.objects.filter(machine=machine)
    if request.method == 'GET':
        serializer = ConditionSerializer(conditions, many=True)
        return JSONResponse(serializer.data)

@csrf_exempt
@validate_api_key
def machine_group(request, pk):
    """
    Retrieve, update or delete a machine group.
    """
    try:
        machine_group = MachineGroup.objects.get(pk=pk)
    except MachineGroup.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = MachineGroupSerializer(machine_group)
        return JSONResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = MachineGroupSerializer(machine_group, data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data)
        return JSONResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        machine_group.delete()
        return HttpResponse(status=204)

@csrf_exempt
@validate_api_key
def machine_group_list(request):
    """
    List all machine groupss, or create a new machine group.
    """
    if request.method == 'GET':
        machine_groups = MachineGroup.objects.all()
        serializer = MachineGroupSerializer(machine_groups, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MachineGroupSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)

@csrf_exempt
@validate_api_key
def business_unit(request, pk):
    """
    Retrieve, update or delete a business unit.
    """
    try:
        business_unit = BusinessUnit.objects.get(pk=pk)
    except BusinessUnit.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = BusinessUnitSerializer(business_unit)
        return JSONResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = BusinessUnitSerializer(business_unit, data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data)
        return JSONResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        business_unit.delete()
        return HttpResponse(status=204)

@csrf_exempt
@validate_api_key
def business_unit_list(request):
    """
    List all business units, or create a new business unit.
    """
    if request.method == 'GET':
        business_units = BusinessUnit.objects.all()
        serializer = BusinessUnitSerializer(business_units, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = BusinessUnitSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)
