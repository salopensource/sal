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
import unicodecsv as csv
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

def is_postgres():
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
        return True
    else:
        return False

def decode_to_string(base64bz2data):
    '''Decodes an inventory submission, which is a plist-encoded
    list, compressed via bz2 and base64 encoded.'''
    try:
        bz2data = base64.b64decode(base64bz2data)
        return bz2.decompress(bz2data)
    except Exception:
        return ''

def unique_apps(inventory, input_type='object'):
    found = []
    for inventory_item in inventory:
        found_flag = False
        if input_type == 'dict':
            for found_item in found:
                if (inventory_item['name'] == found_item['name'] and 
                    inventory_item['version'] == found_item['version'] and
                    inventory_item['bundleid'] == found_item['bundleid'] and 
                    inventory_item['bundlename'] == found_item['bundlename'] and
                    inventory_item['path'] == found_item['path']):
                    found_flag = True
                    break
            if found_flag == False:
                found_item = {}
                found_item['name'] = inventory_item['name']
                found_item['version'] = inventory_item['version']
                found_item['bundleid'] = inventory_item['bundleid']
                found_item['bundlename'] = inventory_item['bundlename']
                found_item['path'] = inventory_item['path']
                found.append(found_item)
        else:
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

@login_required
def inventory_list(request, page='front', theID=None):
    user = request.user
    title=None
    inventory_name = request.GET.get('name')
    inventory_version = request.GET.get('version', '0')
    inventory_bundleid = request.GET.get('bundleid', '')
    inventory_path = request.GET.get('path')
    inventory_bundlename = request.GET.get('bundlename','')
    
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this

        machines = utils.getBUmachines(theID)

    if page == 'group_dashboard' or page == 'machine_group':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)

    if page == 'machine_id':
        machines = Machine.objects.filter(id=theID)

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25
    
    # get the InventoryItems limited to the machines we're allowed to look at
    inventory = InventoryItem.objects.filter(name=inventory_name, version=inventory_version, bundleid=inventory_bundleid, bundlename=inventory_bundlename).filter(machine=machines)[start:end]

    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0

    c = {'user':user, 'machines': machines, 'req_type': page, 'title': title, 'bu_id': theID, 'request':request, 'inventory_name':inventory_name, 'inventory_version':inventory_version, 'inventory_bundleid':inventory_bundleid, 'inventory_bundlename':inventory_bundlename, 'previous_id': previous_id, 'next_id':next_id, 'inventory':inventory }

    return render_to_response('inventory/overview_list_all.html', c, context_instance=RequestContext(request))

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

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25
    #inventory = InventoryItem.objects.all().values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').order_by('name')

    if is_postgres():
        # Woohoo, you're using postgres. Let's make this fast.
        print 'postgres'
        inventory = InventoryItem.objects.all()[start:end].values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').distinct()
    else:
        # Sucks to be you, you're on something else
        inventory = InventoryItem.objects.all().values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').distinct()

        inventory = unique_apps(inventory,'dict')[start:end]

    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0

    c = {'user': request.user, 'inventory': inventory, 'page':'front', 'request': request, 'previous_id': previous_id, 'next_id':next_id}
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))

@login_required
def bu_inventory(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)
    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25
    
    if is_postgres():
        inventory = InventoryItem.objects.filter(machine__machine_group__business_unit=business_unit)[start:end].values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').distinct()
    else:
        inventory = InventoryItem.objects.filter(machine__machine_group__business_unit=business_unit).values('name', 'version', 'path', 'bundleid', 'bundlename', 'id')

        inventory = unique_apps(inventory, 'dict')[start:end]
    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0
    c = {'user': request.user, 'inventory': inventory, 'page':'business_unit', 'business_unit':business_unit, 'request': request, 'previous_id': previous_id, 'next_id':next_id}
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

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25
    if is_postgres():
        inventory = InventoryItem.objects.filter(machine__machine_group=machine_group)[start:end].values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').distinct()
    else:
        inventory = InventoryItem.objects.filter(machine__machine_group=machine_group).values('name', 'version', 'path', 'bundleid', 'bundlename', 'id')
        inventory = unique_apps(inventory, 'dict')[start:end]
    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0
    
    
    c = {'user': request.user, 'inventory': inventory, 'page':'machine_group', 'business_unit':business_unit,'machine_group':machine_group, 'request': request, 'previous_id': previous_id, 'next_id':next_id}
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

    try:
        page = int(request.GET.get('page'))
    except:
        page = 1

    previous_id = page - 1
    next_id = page + 1
    start = (page - 1) * 25
    end = page * 25
    if is_postgres:
        inventory = InventoryItem.objects.filter(machine=machine)[start:end].values('name', 'version', 'path', 'bundleid', 'bundlename', 'id').distinct()
    else:
        inventory = InventoryItem.objects.filter(machine=machine).values('name', 'version', 'path', 'bundleid', 'bundlename', 'id')
        inventory = unique_apps(inventory)[start:end]

    if len(inventory) != 25:
        # we've not got 25 results, probably the last page
        next_id = 0
    
    
    c = {'user': request.user, 'inventory': inventory, 'page':'machine_id', 'business_unit':business_unit,'machine':machine, 'request': request, 'previous_id': previous_id, 'next_id':next_id}
    return render_to_response('inventory/index.html', c, context_instance=RequestContext(request))

@login_required
def export_csv(request, page='front', theID=None):
    user = request.user
    title = 'Inventory Export'
    inventory_name = request.GET.get('name')
    inventory_version = request.GET.get('version', '0')
    inventory_bundleid = request.GET.get('bundleid', '')
    inventory_path = request.GET.get('path')
    inventory_bundlename = request.GET.get('bundlename','')
    # get a list of machines (either from the BU or the group)
    if page == 'front':
        # get all machines
        if user.userprofile.level == 'GA':
            machines = Machine.objects.all()
        else:
            machines = Machine.objects.none()
            for business_unit in user.businessunit_set.all():
                for group in business_unit.machinegroup_set.all():
                    machines = machines | group.machine_set.all()
    if page == 'bu_dashboard':
        # only get machines for that BU
        # Need to make sure the user is allowed to see this
        business_unit = get_object_or_404(BusinessUnit, pk=theID)
        machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

        if machine_groups.count() != 0:
            machines_unsorted = machine_groups[0].machine_set.all()
            for machine_group in machine_groups[1:]:
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        else:
            machines_unsorted = None
        machines=machines_unsorted

    if page == 'group_dashboard':
        # only get machines from that group
        machine_group = get_object_or_404(MachineGroup, pk=theID)
        # check that the user has access to this
        machines = Machine.objects.filter(machine_group=machine_group)

    if page == 'machine_id':
        machines = Machine.objects.filter(id=theID)
    
    # get the InventoryItems limited to the machines we're allowed to look at
    inventoryitems = InventoryItem.objects.filter(name=inventory_name, version=inventory_version, bundleid=inventory_bundleid, bundlename=inventory_bundlename).filter(machine=machines).order_by('name')

    machines = machines.filter(inventoryitem__name=inventory_name, inventoryitem__version=inventory_version, inventoryitem__bundleid=inventory_bundleid, inventoryitem__bundlename=inventory_bundlename)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % title

    writer = csv.writer(response)
    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if not field.is_relation and field.name != 'id' and field.name != 'report' and field.name != 'activity' and field.name != 'os_family':
            header_row.append(field.name)
    header_row.append('business_unit')
    header_row.append('machine_group')
    writer.writerow(header_row)
    for machine in machines:
        row = []
        for name, value in machine.get_fields():
            if name != 'id' and name !='machine_group' and name != 'report' and name != 'activity' and name != 'os_family':
                row.append(value.strip())
        row.append(machine.machine_group.business_unit.name)
        row.append(machine.machine_group.name)
        writer.writerow(row)
        #writer.writerow([machine.serial, machine.machine_group.business_unit.name, machine.machine_group.name,
        #machine.hostname, machine.operating_system, machine.memory, machine.memory_kb, machine.munki_version, machine.manifest])

    return response

@login_required
def list_machines(request, page, name, version, bundleid, bundlename, path, id=None):
    user = request.user
    user_level = user.userprofile.level
    machines = Machine.objects.all()
    if page == 'group':
        group = get_object_or_404(MachineGroup, pk=id)
        machines = machines.filter(machine_group=group)
    elif page == 'bu':
        business_unit = get_object_or_404(BusinessUnit, pk=id)
        machines = machines.filter(machine_group=machine_group__business_unit)
    else:
        if user_level == 'GA':
            machines = machines
        else:
            for business_unit in BusinessUnit.objects.all():
                if business_unit not in user.businessunit_set.all():
                    machines = machines.exclude(machine_group__business_unit = business_unit)