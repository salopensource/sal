import base64
import bz2
import hashlib
import plistlib
from xml.parsers.expat import ExpatError

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import (Http404, HttpRequest, HttpResponse, HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from catalog.models import *
from sal.decorators import *
from server import utils
from server.models import *
from utils.text_utils import decode_to_string


@csrf_exempt
@require_POST
@key_auth_required
def submit_catalog(request):
    submission = request.POST
    key = submission.get('key')
    name = submission.get('name')
    sha = submission.get('sha256hash')
    machine_group = None
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404

        compressed_catalog = submission.get('base64bz2catalog')
        if compressed_catalog:
            catalog_bytes = decode_to_string(compressed_catalog)
            try:
                catalog_plist = plistlib.loads(catalog_bytes)
            except (plistlib.InvalidFileException, ExpatError):
                catalog_plist = None
            if catalog_plist:
                try:
                    catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                except Catalog.DoesNotExist:
                    catalog = Catalog(name=name, machine_group=machine_group)
                catalog.sha256hash = sha
                catalog.content = catalog_str
                catalog.save()
    return HttpResponse("Catalogs submitted.")


@csrf_exempt
@require_POST
@key_auth_required
def catalog_hash(request):
    output = []
    submission = request.POST
    key = submission.get('key')
    catalogs = submission.get('catalogs')
    if key:
        try:
            machine_group = MachineGroup.objects.get(key=key)
        except MachineGroup.DoesNotExist:
            raise Http404
    if catalogs:
        catalogs = decode_to_string(catalogs)
        try:
            catalogs_plist = plistlib.loads(catalogs)
        except (plistlib.InvalidFileException, ExpatError):
            catalogs_plist = None
        if catalogs_plist:
            for item in catalogs_plist:
                name = item['name']
                try:
                    found_catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                    output.append({'name': name, 'sha256hash': found_catalog.sha256hash})
                except Catalog.DoesNotExist:
                    output.append({'name': name, 'sha256hash': 'NOT FOUND'})

    return HttpResponse(plistlib.dumps(output).decode())
