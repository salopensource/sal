from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import RequestContext, Template, Context
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import Http404
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django import forms
from django.db.models import Q
from django.db.models import Count
from server import utils
from django.shortcuts import render_to_response, get_object_or_404, redirect

import plistlib
import base64
import bz2
import hashlib
import json

from datetime import datetime
import urllib2
from xml.etree import ElementTree

from models import *
from server.models import *

def decode_to_string(base64bz2data):
    '''Decodes an inventory submission, which is a plist-encoded
    list, compressed via bz2 and base64 encoded.'''
    try:
        bz2data = base64.b64decode(base64bz2data)
        return bz2.decompress(bz2data)
    except Exception:
        return ''

def unique_apps(inventory):
    found = []
    for inventory_item in inventory:
        found_flag = False
        for found_item in found:
            if (inventory_item.name == found_item['name'] and 
                inventory_item.version == found_item['version'] and
                inventory_item.bundleid == found_item['bundleid'] and 
                inventory_item.bundlename == found_item['bundlename'] and
                inventory_item.path == found_item['path']):
                found_flag = True
                break
        if found_flag == False:
            found_item = {}
            found_item['name'] = inventory_item.name
            found_item['version'] = inventory_item.version
            found_item['bundleid'] = inventory_item.bundleid
            found_item['bundlename'] = inventory_item.bundlename
            found_item['path'] = inventory_item.path
            found.append(found_item)
    return found

@csrf_exempt
def inventory_submit(request):
    if request.method != 'POST':
        raise Http404
    
    # list of bundleids to ignore
    bundleid_ignorelist = [
        'com.apple.print.PrinterProxy'
    ]
    submission = request.POST
    serial = submission.get('serial')
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            raise Http404

        compressed_inventory = submission.get('base64bz2inventory')
        if compressed_inventory:
            compressed_inventory = compressed_inventory.replace(" ", "+")
            inventory_str = decode_to_string(compressed_inventory)
            try:
                inventory_list = plistlib.readPlistFromString(inventory_str)
            except Exception:
                inventory_list = None
            if inventory_list:
                try:
                    inventory_meta = Inventory.objects.get(machine=machine)
                except Inventory.DoesNotExist:
                    inventory_meta = Inventory(machine=machine)
                inventory_meta.sha256hash = \
                    hashlib.sha256(inventory_str).hexdigest()
                # clear existing inventoryitems
                machine.inventoryitem_set.all().delete()
                # insert current inventory items
                for item in inventory_list:
                    # skip items in bundleid_ignorelist.
                    if not item.get('bundleid') in bundleid_ignorelist:
                        i_item = machine.inventoryitem_set.create(
                            name=item.get('name', ''),
                            version=item.get('version', ''),
                            bundleid=item.get('bundleid', ''),
                            bundlename=item.get('CFBundleName', ''),
                            path=item.get('path', '')
                            )
                machine.last_inventory_update = datetime.now()
                inventory_meta.save()
            machine.save()
            return HttpResponse(
                "Inventory submmitted for %s.\n" %
                submission.get('serial'))
    
    return HttpResponse("No inventory submitted.\n")


def inventory_hash(request, serial):
    sha256hash = ''
    machine = None
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
            inventory_meta = Inventory.objects.get(machine=machine)
            sha256hash = inventory_meta.sha256hash
        except (Machine.DoesNotExist, Inventory.DoesNotExist):
            pass
    else:
        return HttpResponse("MACHINE NOT FOUND")
    return HttpResponse(sha256hash)


@login_required
def index(request):
    # This really should just select on the BU's the user has access to like the
    # Main page, but this will do for now
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    inventory = InventoryItem.objects.all()
    found = unique_apps(inventory)

    c = {'user': request.user, 'inventory': found, 'page':'front', 'request': request }
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))

@login_required
def bu_inventory(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)
    # Get the groups within the Business Unit
    machines = utils.getBUmachines(bu_id)

    inventory = []
    for machine in machines:
        for item in machine.inventoryitem_set.all():
            inventory.append(item)
    
    found = unique_apps(inventory)
    c = {'user': request.user, 'inventory': found, 'page':'business_unit', 'business_unit':business_unit, 'request': request}
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))

@login_required
def machine_group_inventory(request, group_id):
    user = request.user
    user_level = user.userprofile.level
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)

    inventory = []
    for machine in machine_group.machine_set.all():
        for item in machine.inventoryitem_set.all():
            inventory.append(item)
    
    found = unique_apps(inventory)
    c = {'user': request.user, 'inventory': found, 'page':'machine_group', 'business_unit':business_unit, 'request': request}
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))

@login_required
def machine_inventory(request, machine_id):
    user = request.user
    user_level = user.userprofile.level
    machine = get_object_or_404(Machine, pk=machine_id)
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)

    inventory = []
    for item in machine.inventoryitem_set.all():
        inventory.append(item)
    
    found = unique_apps(inventory)
    c = {'user': request.user, 'inventory': found, 'page':'machine', 'business_unit':business_unit, 'request': request}
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))