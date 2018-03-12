import base64
import bz2
import hashlib
import plistlib

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import (Http404, HttpRequest, HttpResponse, HttpResponseRedirect)
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, RequestContext, Template
from django.template.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt

from models import *
from sal.decorators import *
from server import utils
from server.models import *
from server.text_utils import decode_to_string


@csrf_exempt
@key_auth_required
def submit_catalog(request):
    if request.method != 'POST':
        raise Http404

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
        # print compressed_catalog
        if compressed_catalog:
            # compressed_catalog = compressed_catalog.replace(" ", "+")
            catalog_str = decode_to_string(compressed_catalog)
            print catalog_str
            try:
                catalog_plist = plistlib.readPlistFromString(catalog_str)
            except Exception:
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
@key_auth_required
def catalog_hash(request):
    if request.method != 'POST':
        print 'method not post'
        raise Http404

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
            catalogs_plist = plistlib.readPlistFromString(catalogs)
        except Exception:
            catalogs_plist = None
        if catalogs_plist:
            for item in catalogs_plist:
                name = item['name']
                try:
                    found_catalog = Catalog.objects.get(name=name, machine_group=machine_group)
                    output.append({'name': name, 'sha256hash': found_catalog.sha256hash})
                except Catalog.DoesNotExist:
                    output.append({'name': name, 'sha256hash': 'NOT FOUND'})

    return HttpResponse(plistlib.writePlistToString(output))
