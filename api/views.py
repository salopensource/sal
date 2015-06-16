from models import *
from server.models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.core import serializers
from django.core.exceptions import PermissionDenied

import json

def get_machine_facts(machine):
    output = {}
    for fact in machine.fact_set.all():
        output[fact.fact_name] = fact.fact_data
    return output

def get_machine_conditions(machine):
    output = {}
    for condition in machine.condition_set.all():
        output[condition.condition_name] = condition.condition_data
    return output

def clean_serialize(data):
    output = []
    temp = json.loads(data)
    for item in temp:
        if item['model'] == 'server.machine':
            # working on a machine, get it's group and business Unit
            machine = get_object_or_404(Machine, pk=item['pk'])
            machine_group = machine.machine_group
            business_unit = machine_group.business_unit
            item['fields']['machine_group_name'] = machine_group.name
            item['fields']['business_unit_name'] = business_unit.name
            item['fields']['business_unit'] = business_unit.id

            item['fields']['facts'] = get_machine_facts(machine)

            if machine.condition_set.all():
                item['fields']['conditions'] = get_machine_conditions(machine)
            else:
                item['fields']['conditions'] = []
        item['fields']['id'] = item['pk']
        output.append(item['fields'])
    return output

def validate_request(request, readwrite=False):
    if 'public_key' not in request.POST or 'private_key' not in request.POST:
        raise Http404
    # Get the API key
    public_key = request.POST['public_key']
    private_key = request.POST['private_key']
    api_key = ApiKey.objects.get(private_key=private_key, public_key=public_key)
    if not api_key:
        raise PermissionDenied()
    else:
        if readwrite == True:
            print api_key
            if api_key.read_only == False:
                return True
            else:
                raise PermissionDenied()
        else:
            return True

@csrf_exempt
def v1_machines(request):
    validate_request(request)
    machines = Machine.objects.all().prefetch_related()
    if request.POST:
        if 'data' in request.POST:
            # comma separated serials, trim after splitting
            data = request.POST['data']
            data = json.loads(data)
            serials = data['data']['serials']
            machines = machines.filter(serial__in=serials)
    machines = clean_serialize(serializers.serialize('json', machines))
    return HttpResponse(json.dumps(machines), content_type="application/json")

@csrf_exempt
def v1_create_machine(request):
    validate_request(request, True)
    if 'data' in request.POST:
        data = request.POST['data']
        data = json.loads(data)
        if 'machine_group' in data:
            try:
                machine_group = MachineGroup.objects.get(pk=int(data['machine_group']))
            except:
                response = {'error':'Machine group with ID %s not found.' % rdata['machine_group']}
                return HttpResponse(json.dumps(response), content_type="application/json")
        else:
            response = {'error':'Machine group not in POST data.'}
            return HttpResponse(json.dumps(response), content_type="application/json")

        if 'serial' in data:
            serial = data['serial']
            machine_count = Machine.objects.filter(serial=serial).count()

            if machine_count != 0:
                response = {'error':'Machine with serial %s already exists.' % serial}
                return HttpResponse(json.dumps(response), content_type="application/json")
            else:
                machine = Machine(serial=serial, machine_group=machine_group)
                machine.save()
                machines = []
                machines.append(machine)
                response = clean_serialize(serializers.serialize('json', machines))
    else:
        response = {'error':'No data sent.'}

    return HttpResponse(json.dumps(response), content_type="application/json")
