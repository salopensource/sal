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

def clean_serialize(data):
    output = []
    temp = json.loads(data)
    for item in temp:
        output.append(item['fields'])
    return output

def validate_request(request):
    if 'public_key' not in request.POST or 'private_key' not in request.POST:
        raise Http404
    # Get the API key
    public_key = request.POST['public_key']
    private_key = request.POST['private_key']
    api_key = ApiKey.objects.filter(private_key=private_key, public_key=public_key)
    if not api_key:
        raise PermissionDenied()
    else:
        return True

@csrf_exempt
def v1_machines(request):
    validate_request(request)
    machines = Machine.objects.all()
    if 'serials' in request.POST:
        # comma separated serials, trim after splitting
        serials = request.POST['serials']
        serials = [x.strip() for x in serials.split(',')]
        print serials
        machines = machines.filter(serial__in=serials)
    machines = clean_serialize(serializers.serialize('json', machines))
    return HttpResponse(json.dumps(machines), content_type="application/json")
