# Create your views here.
from models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from datetime import datetime, timedelta, date
from django.db.models import Count
from django.contrib import messages
import plistlib
import ast
from forms import *
import pprint
import re
import os

def load_widgets():
    # iterate over all widgets in the directory
    widget_dir = settings.WIDGETS_DIR
    for dirname, dirnames, filenames in os.walk(widget_dir):
        # print path to all filenames.
        for filename in filenames:
            plist = None
            filePath = os.path.join(dirname, filename)
            # Try to load it as a plist
            try:
                plist = plistlib.readPlist(filePath)
            except:
                pass
                
            if plist:
                # if it's a valid plist, see if it's in the database
                try:
                    # if it exists, select it
                    widget = Widget.objects.get(name=plist['name'])
                except Widget.DoesNotExist:
                    widget = Widget(name=plist['name'])
                # Set the fields
                widget.description = plist['description']
                widget.display_name = plist['display_name']
                widget.source = plist['source']
                widget.widget_type = plist['widget_type']
                widget.search_item = plist['search_item']
                if plist['widget_type'] == 'traffic_light':
                    widget.ok_label = plist['ok'][0]['label']
                    widget.ok_search_operator = plist['ok'][0]['search_operator']
                    widget.ok_search_value = plist['ok'][0]['search_value']
                    widget.warning_label = plist['warning'][0]['label']
                    widget.warning_search_operator = plist['warning'][0]['search_operator']
                    widget.warning_search_value = plist['warning'][0]['search_value']
                    widget.alert_label = plist['alert'][0]['label']
                    widget.alert_search_value = plist['alert'][0]['search_value']
                    widget.alert_search_operator = plist['alert'][0]['search_operator']
                # Save it
                widget.save()
                
                     
    
    # for each one in the db, loop over plists. If it's not in there, delete from the db

@login_required
def widgetToTopList(request):
    user = request.user
    user_level = user.userprofile.level
    load_widgets()
    if user_level != 'GA':
        return redirect(index)
    widgets = Widget.objects.all()
    assigned_widgets = TopWidget.objects.all()
    for widget in widgets:
        # Is this widget already assigned?
        for assigned_widget in assigned_widgets:
            if widget.id == assigned_widget.widget.id:
                # if it's already assigned, remove it from the lsit
                widgets = widgets.exclude(id=widget.id)
    c = {'user': user, 'widgets':widgets, 'assigned_widgets':assigned_widgets}
    return render_to_response('server/widgetToTop.html', c, context_instance=RequestContext(request))

@login_required
def widgetToTopAdd(request, widget_id):
    user = request.user
    user_level = user.userprofile.level
    load_widgets()
    if user_level != 'GA':
        return redirect(index)
    # make sure it's not been added already
    widget = get_object_or_404(Widget, pk=widget_id)
    try:
        top_widget = TopWidget.objects.get(widget=widget)
    except TopWidget.DoesNotExist:
        # get the widget with that ID
        top_widget = TopWidget(widget=widget)
        top_widget.save()
    return redirect(widgetToTopList)
    
@login_required
def widgetToTopRemove(request, widget_id):
    user = request.user
    user_level = user.userprofile.level
    load_widgets()
    if user_level != 'GA':
        return redirect(index)
    # make sure it's not been added already
    widget = get_object_or_404(Widget, pk=widget_id)
    try:
        top_widget = TopWidget.objects.filter(widget=widget).delete()
    except TopWidget.DoesNotExist:
        # if it didn't delete, it's probably already gone
        pass
    return redirect(widgetToTopList)

def processWidget(request, machines, widgetName):
    # Get widget
    output = {}
    widget = get_object_or_404(Widget, name=widgetName)
    # handle the types of widget
    # list
    output['displayname'] = widget.display_name
    output['type'] = widget.widget_type
    output['search_item'] = widget.search_item
    output['name'] = widget.name
    if widget.widget_type == 'list_count':
        #Source - builtin or Facter?
        if widget.source == 'builtin':
            output['machines'] = machines.extra(select={'data_value':widget.search_item}).values(widget.search_item, 'data_value').annotate(count=Count(widget.search_item))
        if widget.source == 'facter':
            search_field = 'fact__fact_name'
            output['machines'] = machines.filter(fact__fact_name=widget.search_item).count()
    
    # warning lights
    if widget.widget_type == 'traffic_light':
        if widget.source == 'builtin':
            # ok label and search
            output['ok_label'] = widget.ok_label
            kwargs = {}
            if widget.ok_search_operator == 'range':
                search_value = widget.ok_search_value.split(',')
            else:
                search_value = widget.ok_search_value
            if widget.ok_search_operator:
                kwargs[ widget.search_item + '__' + widget.ok_search_operator ] = search_value
            else:
                kwargs[ widget.search_item ] = widget.ok_search_value
            output['ok_machines'] = machines.filter(**kwargs).count()

            # warning label and search
            output['warning_label'] = widget.warning_label
            kwargs = {}
            # if it's a range, split on comma, trim the spaces and use both values
            if widget.warning_search_operator == 'range':
                search_value = widget.warning_search_value.split(',')
            else:
                search_value = widget.warning_search_value
            if widget.warning_search_operator:
                kwargs[ widget.search_item + '__' + widget.warning_search_operator ] = search_value
            else:
                kwargs[ widget.search_item ] = widget.warning_search_value
            output['warning_machines'] = machines.filter(**kwargs).count()
            
            # alert label and search
            output['alert_label'] = widget.alert_label
            kwargs = {}
            if widget.alert_search_operator == 'range':
                search_value = widget.alert_search_value.split(',')
            else:
                search_value = widget.alert_search_value
            if widget.alert_search_operator:
                kwargs[ widget.search_item + '__' + widget.alert_search_operator ] = search_value
            else:
                kwargs[ widget.search_item ] = widget.alert_search_value
            output['alert_machines'] = machines.filter(**kwargs).count()
    print output
    return output
    
def getWidgetMachines(request, machines, widgetName, data):
    '''Outputs a queryset of Machine objects when passed a widget name and search data'''
    # Get widget
    output = {}
    widget = get_object_or_404(Widget, name=widgetName)
    if widget.widget_type == 'list_count':
        kwargs[ widget.search_item ] = data
        #Source - builtin or Facter?
        if widget.source == 'builtin':
            output = Machine.objects.filter(**kwargs)
        if widget.source == 'facter':
            search_field = 'fact__fact_name'
            output['machines'] = Machine.objects.filter(fact__fact_name=widget.search_item, fact__fact_data=data)
    
    # warning lights
    return output
    
def getWidgets(request, item_type, item_id=None):
    # handle the various types
    output = []
    if item_type == 'top':
        # get the list of widgets for the type
        widgets = TopWidget.objects.all()
        # get the machines
        # if you're not GA, you shouldn't be here
        user_level = request.user.userprofile.level
        if user_level != 'GA':
            return redirect(index)
        machines = Machine.objects.all()
        # loop over the widgets
        for widget in widgets:
            output.append(processWidget(request, machines, widget.widget.name))
            #output = output.append(processWidget(request, machines, widget.widget.name))
    #print output
    return output 

@login_required 
def index(request):
    # Get the current user's Business Units
    user = request.user
    user_level = user.userprofile.level
    load_widgets()
    if user_level != 'GA':
        # user has many BU's display them all in a friendly manner
        business_units = user.businessunit_set.all()
    
        # Later on, get the latest BU the user has looked at and dump them there
        for bu in user.businessunit_set.all():
            return redirect('server.views.bu_dashboard', bu_id=bu.id)
            break
    else:
        
        business_units = BusinessUnit.objects.all()
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        three_months_ago = today - timedelta(days=90)
        machine_data = {}
        
        mem_4_gb = 4 * 1024 * 1024
        mem_415_gb = 4.15 * 1024 * 1024
        mem_775_gb = 7.75 * 1024 * 1024
        mem_8_gb = 8 * 1024 * 1024
        os_info = None
        if user_level == 'GA':
            #os_info = Machine.objects.all().values('operating_system').annotate(count=Count('operating_system'))
            
            widget_results = getWidgets(request, 'top')
            machine_data['checked_in_this_hour'] = Machine.objects.filter(last_checkin__gte=hour_ago).count()
            machine_data['checked_in_today'] = Machine.objects.filter(last_checkin__gte=today).count()
            machine_data['checked_in_this_week'] = Machine.objects.filter(last_checkin__gte=week_ago).count()
            machine_data['inactive_for_a_month'] = Machine.objects.filter(last_checkin__range=(three_months_ago, month_ago)).count()
            machine_data['inactive_for_three_months'] = Machine.objects.exclude(last_checkin__gte=three_months_ago).count()
            machine_data['errors'] = Machine.objects.filter(errors__gt=0).count()
            machine_data['warnings'] = Machine.objects.filter(warnings__gt=0).count()
            machine_data['activity'] = Machine.objects.filter(activity__isnull=False).count()
            machine_data['disk_ok'] = Machine.objects.filter(hd_percent__lt=80).count()
            machine_data['disk_warning'] = Machine.objects.filter(hd_percent__range=["80", "89"]).count()
            machine_data['disk_alert'] = Machine.objects.filter(hd_percent__gte=90).count()
            machine_data['mem_ok'] = Machine.objects.filter(memory_kb__gte=mem_8_gb).count()
            machine_data['mem_warning'] = Machine.objects.filter(memory_kb__range=[mem_4_gb, mem_775_gb]).count()
            machine_data['mem_alert'] = Machine.objects.filter(memory_kb__lt=mem_4_gb).count()
            machine_data['uptime_ok'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1).count()
            machine_data['uptime_warning'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7]).count()
            machine_data['uptime_alert'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7).count()
            
            pending_updates = PendingUpdate.objects.values('update', 'update_version', 'display_name').annotate(count=Count('update'))
            
            pending_apple_updates = PendingAppleUpdate.objects.values('update', 'update_version', 'display_name').annotate(count=Count('update'))
        else:
            updates = []
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    updates.extend(PendingUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update')))
            pending_updates = updates
            
            updates = []
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    updates.extend(PendingAppleUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update')))
            pending_apple_updates = updates
            osen = []
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    osen.extend(Machine.objects.filter(machine_group=machine_group).values('operating_system').annotate(count=Count('operating_system')))
            os_info = osen
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(last_checkin__gte=hour_ago, machine_group=machine_group).count()
            machine_data['checked_in_this_hour'] = count
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(last_checkin__gte=today, machine_group=machine_group).count()
            machine_data['checked_in_today'] = count
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(last_checkin__gte=week_ago, machine_group=machine_group).count()
            machine_data['checked_in_this_week'] = count
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(last_checkin__range=(three_months_ago, month_ago), machine_group=machine_group).count()
            machine_data['inactive_for_a_month'] = count
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.exclude(last_checkin__gte=three_months_ago).filter(machine_group=machine_group).count()
            machine_data['inactive_for_three_months'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(errors__gt=0, machine_group=machine_group).count()
            machine_data['errors'] = count
                    
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(warnings__gt=0, machine_group=machine_group).count()
            machine_data['warnings'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(activity__isnull=False, machine_group=machine_group).count()
            machine_data['activity'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(hd_percent__lt=80, machine_group=machine_group).count()
            machine_data['disk_ok'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(hd_percent__range=["80", "89"], machine_group=machine_group).count()
            machine_data['disk_warning'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(hd_percent__gte=90, machine_group=machine_group).count()
            machine_data['disk_alert'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(memory_kb__gte=mem_8_gb, machine_group=machine_group).count()
            machine_data['mem_ok'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(memory_kb__range=[mem_4_gb, mem_775_gb], machine_group=machine_group).count()
            machine_data['mem_warning'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(memory_kb__lt=mem_4_gb, machine_group=machine_group).count()
            machine_data['mem_alert'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1, machine_group=machine_group).count()
            machine_data['uptime_ok'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7], machine_group=machine_group).count()
            machine_data['uptime_warning'] = count
            
            count = 0
            for bu in business_units:
                for machine_group in bu.machinegroup_set.all():
                    count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7, machine_group=machine_group).count()
            machine_data['uptime_alert'] = count
            
            
    c = {'user': request.user, 'business_units': business_units, 'machine_data': machine_data, 'os_info':os_info, 'pending_updates':pending_updates, 'pending_apple_updates':pending_apple_updates, 'widget_results':widget_results}
    return render_to_response('server/index.html', c, context_instance=RequestContext(request)) 

# New BU
@login_required
def new_business_unit(request):
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = BusinessUnitForm(request.POST)
        if form.is_valid():
            new_business_unit = form.save(commit=False)
            new_business_unit.save()
            form.save_m2m()
            return redirect('bu_dashboard', new_business_unit.id)
    else:
        form = BusinessUnitForm()
    c = {'form': form}
    user = request.user
    user_level = user.userprofile.level
    if user_level != 'GA':
        return redirect(index)
    return render_to_response('forms/new_business_unit.html', c, context_instance=RequestContext(request))
# Edit BU
 
# BU Dashboard
@login_required 
def bu_dashboard(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    bu = business_unit
    if business_unit not in user.businessunit_set.all() and user_level != 'GA':
        print 'not letting you in ' + user_level
        return redirect(index)
    # Get the groups within the Business Unit
    machine_groups = business_unit.machinegroup_set.all()
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False
    
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    mem_4_gb = 4 * 1024 * 1024
    mem_415_gb = 4.15 * 1024 * 1024
    mem_775_gb = 7.75 * 1024 * 1024
    mem_8_gb = 8 * 1024 * 1024
    from itertools import chain
    machine_data = {}
    os_info = []
    # osen = []
    for machine_group in machine_groups:

        osen = Machine.objects.filter(machine_group=machine_group).values('operating_system').annotate(count=Count('operating_system'))
        for item in osen:
            # loop over existing items, see if there is a dict with the right value
            found = False
            for os in os_info:
                if os['operating_system'] == item['operating_system']:
                    os['count'] = os['count'] + item['count']
                    found = True
                    break
            if found == False:
                os_info.append(item)
                
    
    pending_apple_updates = []
    for machine_group in machine_groups:

        updates = PendingAppleUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update'))
        for item in updates:
            # loop over existing items, see if there is a dict with the right value
            found = False
            for update in pending_apple_updates:
                if update['update'] == item['update']:
                    update['count'] = update['count'] + item['count']
                    found = True
                    break
            if found == False:
                pending_apple_updates.append(item)
                
    pending_updates = []
    for machine_group in machine_groups:

        updates = PendingUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update'))
        for item in updates:
            # loop over existing items, see if there is a dict with the right value
            found = False
            for update in pending_updates:
                if update['update'] == item['update']:
                    update['count'] = update['count'] + item['count']
                    found = True
                    break
            if found == False:
                pending_updates.append(item)
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(last_checkin__gte=hour_ago, machine_group=machine_group).count()
    machine_data['checked_in_this_hour'] = count

    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(last_checkin__gte=today, machine_group=machine_group).count()
    machine_data['checked_in_today'] = count
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(last_checkin__gte=week_ago, machine_group=machine_group).count()
    machine_data['checked_in_this_week'] = count
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(last_checkin__range=(three_months_ago, month_ago), machine_group=machine_group).count()
    machine_data['inactive_for_a_month'] = count
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.exclude(last_checkin__gte=three_months_ago).filter(machine_group=machine_group).count()
    machine_data['inactive_for_three_months'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(errors__gt=0, machine_group=machine_group).count()
    machine_data['errors'] = count
            
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(warnings__gt=0, machine_group=machine_group).count()
    machine_data['warnings'] = count
    
    count = 0
    
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(activity__isnull=False, machine_group=machine_group).count()
    machine_data['activity'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(hd_percent__lt=80, machine_group=machine_group).count()
    machine_data['disk_ok'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(hd_percent__range=["80", "89"], machine_group=machine_group).count()
    machine_data['disk_warning'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(hd_percent__gte=90, machine_group=machine_group).count()
    machine_data['disk_alert'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(memory_kb__gte=mem_8_gb, machine_group=machine_group).count()
    machine_data['mem_ok'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(memory_kb__range=[mem_4_gb, mem_775_gb], machine_group=machine_group).count()
    machine_data['mem_warning'] = count
    
    count = 0
    for machine_group in machine_groups:
        count = count + Machine.objects.filter(memory_kb__lt=mem_4_gb, machine_group=machine_group).count()
    machine_data['mem_alert'] = count
    
    count = 0
    for machine_group in bu.machinegroup_set.all():
        count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1, machine_group=machine_group).count()
    machine_data['uptime_ok'] = count
    
    count = 0
    for machine_group in bu.machinegroup_set.all():
        count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7], machine_group=machine_group).count()
    machine_data['uptime_warning'] = count
    
    count = 0
    for machine_group in bu.machinegroup_set.all():
        count = count + Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7, machine_group=machine_group).count()
    machine_data['uptime_alert'] = count
    
    c = {'user': request.user, 'machine_groups': machine_groups, 'is_editor': is_editor, 'business_unit': business_unit, 'os_info': os_info, 'machine_data': machine_data, 'user_level': user_level, 'pending_apple_updates': pending_apple_updates, 'pending_updates': pending_updates}
    return render_to_response('server/bu_dashboard.html', c, context_instance=RequestContext(request))

# Overview list (all)
@login_required
def overview_list_all(request, req_type, data, bu_id=None):
    # get all the BU's that the user has access to
    user = request.user
    user_level = user.userprofile.level
    operating_system = None
    activity = None
    inactivity = None
    disk_space = None
    widget = None
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    mem_4_gb = 4 * 1024 * 1024
    mem_415_gb = 4.15 * 1024 * 1024
    mem_775_gb = 7.75 * 1024 * 1024
    mem_8_gb = 8 * 1024 * 1024
    
    # Select the appropriate machines
    if bu_id != None:
        business_units = get_object_or_404(BusinessUnit, pk=bu_id)
        machine_groups = MachineGroup.objects.filter(business_unit=business_units).prefetch_related('machine_set').all()

        machines_unsorted = machine_groups[0].machine_set.all()
        for machine_group in machine_groups[1:]:
            machines_unsorted = machines_unsorted | machine_group.machine_set.all()
        all_machines=machines_unsorted
        # check user is allowed to see it
        if business_units not in user.businessunit_set.all():
            if user_level != 'GA':
                print 'not letting you in ' + user_level
                return redirect(index)
    else:
        # all BUs the user has access to
        business_units = user.businessunit_set.all()
        # get all the machine groups
        # business_unit = business_units[0].machinegroup_set.all()
        machines_unsorted = Machine.objects.none()
        for business_unit in business_units:
            for machine_group in business_unit.machinegroup_set.all():
                machines_unsorted = machines_unsorted | machine_group.machine_set.all()

        all_machines = machines_unsorted
        if user_level == 'GA':
            business_units = BusinessUnit.objects.all()
            all_machines = Machine.objects.all()
    # Try and get a widget with the name
    try:
        widget = Widget.objects.get(name=req_type)
    except:
        pass
        
    if widget:
        machines = getWidgetMachines(request, all_machines, widget.name, data)
    
    if req_type == 'activity':
        activity = data
    
    if req_type == 'inactivity':
        inactivity = data
        
    if req_type == 'disk_space_ok':
        disk_space_ok = data
        
    if req_type == 'disk_space_warning':
        disk_space_warning = data
    
    if req_type == 'disk_space_alert':
        disk_space_alert = data
        
    if req_type == 'mem_ok':
        disk_space_alert = data

    if req_type == 'mem_warning':
        disk_space_alert = data
    
    if req_type == 'mem_alert':
        disk_space_alert = data
    
    if req_type == 'pending_updates':
        pending_update = data
    
    if req_type == 'pending_apple_updates':
        pending_apple_update = data
            
    if req_type == 'errors':
        machines = all_machines.filter(errors__gt=0)
    
    if req_type == 'warnings':
        machines = all_machines.filter(warnings__gt=0)
    
    if req_type == 'active':
        machines = all_machines.filter(activity__isnull=False)
    
    if req_type == 'disk_space_ok':
        machines = all_machines.filter(hd_percent__lt=80)
    
    if req_type == 'disk_space_warning':
        machines = all_machines.filter(hd_percent__range=["80", "89"])
    
    if req_type == 'disk_space_alert':
        machines = all_machines.filter(hd_percent__gte=90)
    
    if req_type == 'mem_ok':
        machines = all_machines.filter(memory_kb__gte=mem_8_gb)
    
    if req_type == 'mem_warning':
        machines = all_machines.filter(memory_kb__range=[mem_4_gb, mem_775_gb])
        
    if req_type == 'mem_alert':
        machines = all_machines.filter(memory_kb__lt=mem_4_gb)
    
    if req_type == 'uptime_ok':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1)
    
    if req_type == 'uptime_warning':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7])
    
    if req_type == 'uptime_alert':
        machines = all_machines.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7)
    
    if activity is not None:
        if data == '1-hour':
            machines = all_machines.filter(last_checkin__gte=hour_ago)
        if data == 'today':
            machines = all_machines.filter(last_checkin__gte=today)
        if data == '1-week':
            machines = all_machines.filter(last_checkin__gte=week_ago)
    if inactivity is not None:
        if data == '1-month':
            machines = all_machines.filter(last_checkin__range=(three_months_ago, month_ago))
        if data == '3-months':
            machines = all_machines.exclude(last_checkin__gte=three_months_ago)
    
    if req_type == 'pending_updates':
        machines = all_machines.filter(pendingupdate__update=pending_update)
        
    if req_type == 'pending_apple_updates':
        machines = all_machines.filter(pendingappleupdate__update=pending_apple_update)
    c = {'user':user, 'machines': machines, 'req_type': req_type, 'data': data, 'bu_id': bu_id }
    
    return render_to_response('server/overview_list_all.html', c, context_instance=RequestContext(request))

# Machine Group Dashboard
@login_required 
def group_dashboard(request, group_id):
    # check user is allowed to access this
    user = request.user
    user_level = user.userprofile.level
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False   
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    mem_4_gb = 4 * 1024 * 1024
    mem_415_gb = 4.15 * 1024 * 1024
    mem_775_gb = 7.75 * 1024 * 1024
    mem_8_gb = 8 * 1024 * 1024
    
    os_info = Machine.objects.filter(machine_group=machine_group).values('operating_system').annotate(count=Count('operating_system'))
    
    pending_updates = PendingUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update'))
    
    pending_apple_updates = PendingAppleUpdate.objects.filter(machine__machine_group=machine_group).values('update', 'update_version', 'display_name').annotate(count=Count('update'))
    
    machine_data = {}
    machine_data['errors'] = Machine.objects.filter(errors__gt=0, machine_group=machine_group).count()
    machine_data['warnings'] = Machine.objects.filter(warnings__gt=0, machine_group=machine_group).count()
    machine_data['activity'] = Machine.objects.filter(activity__isnull=False, machine_group=machine_group).count()
    machine_data['checked_in_this_hour'] = Machine.objects.filter(last_checkin__gte=hour_ago, machine_group=machine_group).count()
    machine_data['checked_in_today'] = Machine.objects.filter(last_checkin__gte=today, machine_group=machine_group).count()
    machine_data['checked_in_this_week'] = Machine.objects.filter(last_checkin__gte=week_ago, machine_group=machine_group).count()
    machine_data['inactive_for_a_month'] = Machine.objects.filter(last_checkin__range=(three_months_ago, month_ago), machine_group=machine_group).count()
    machine_data['inactive_for_three_months'] = Machine.objects.exclude(last_checkin__gte=three_months_ago).filter(machine_group=machine_group).count()
    machine_data['disk_ok'] = Machine.objects.filter(hd_percent__lt=80).filter(machine_group=machine_group).count()
    machine_data['disk_warning'] = Machine.objects.filter(hd_percent__range=["80", "89"]).filter(machine_group=machine_group).count()
    machine_data['disk_alert'] = Machine.objects.filter(hd_percent__gte=90).filter(machine_group=machine_group).count()
    machine_data['mem_ok'] = Machine.objects.filter(memory_kb__gte=mem_8_gb).filter(machine_group=machine_group).count()
    machine_data['mem_warning'] = Machine.objects.filter(memory_kb__range=[mem_4_gb, mem_775_gb]).filter(machine_group=machine_group).count()
    machine_data['mem_alert'] = Machine.objects.filter(memory_kb__lt=mem_4_gb).filter(machine_group=machine_group).count()
    machine_data['uptime_ok'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1).filter(machine_group=machine_group).count()
    machine_data['uptime_warning'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7]).filter(machine_group=machine_group).count()
    machine_data['uptime_alert'] = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7).filter(machine_group=machine_group).count()
    c = {'user': request.user, 'machine_group': machine_group, 'user_level': user_level, 'machine_data':machine_data, 'is_editor': is_editor, 'business_unit': business_unit, 'os_info':os_info, 'pending_updates':pending_updates, 'pending_apple_updates':pending_apple_updates}
    return render_to_response('server/group_dashboard.html', c, context_instance=RequestContext(request))

# New Group
@login_required
def new_machine_group(request, bu_id):
    c = {}
    c.update(csrf(request))
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    if request.method == 'POST':
        form = MachineGroupForm(request.POST)
        if form.is_valid():
            new_machine_group = form.save(commit=False)
            new_machine_group.business_unit = business_unit
            new_machine_group.save()
            #form.save_m2m()
            return redirect('group_dashboard', new_machine_group.id)
    else:
        form = MachineGroupForm()
    
    user = request.user
    user_level = user.userprofile.level
    if user_level == 'GA' or user_level == 'RW':
        is_editor = True
    else:
        is_editor = False 
        
    if business_unit not in user.businessunit_set.all() or is_editor == False:
        return redirect(index)
    c = {'form': form, 'is_editor': is_editor, 'business_unit': business_unit, }   
    return render_to_response('forms/new_machine_group.html', c, context_instance=RequestContext(request))

# Edit Group

# Delete Group

# Overview list (group)
@login_required
def overview_list_group(request, group_id, req_type, data):
    machine_group = get_object_or_404(MachineGroup, pk=group_id)
    business_unit = machine_group.business_unit
    operating_system = None
    activity = None
    inactivity = None
    user = request.user
    user_level = user.userprofile.level
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)
    
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    three_months_ago = today - timedelta(days=90)
    mem_4_gb = 4 * 1024 * 1024
    mem_415_gb = 4.15 * 1024 * 1024
    mem_775_gb = 7.75 * 1024 * 1024
    mem_8_gb = 8 * 1024 * 1024
    
    if req_type == 'operating_system':
        operating_system = data
    
    if req_type == 'activity':
        activity = data
    
    if req_type == 'inactivity':
        inactivity = data
        
    if req_type == 'pending_updates':
        pending_update = data
    
    if req_type == 'pending_apple_updates':
        pending_apple_update = data
        
    if activity is not None:
        if data == '1-hour':
            machines = Machine.objects.filter(last_checkin__gte=hour_ago, machine_group=machine_group)
        if data == 'today':
            machines = Machine.objects.filter(last_checkin__gte=today, machine_group=machine_group)
        if data == '1-week':
            machines = Machine.objects.filter(last_checkin__gte=week_ago, machine_group=machine_group)
    if inactivity is not None:
        if data == '1-month':
            machines = Machine.objects.filter(last_checkin__range=(three_months_ago, month_ago), machine_group=machine_group)
        if data == '3-months':
            machines = Machine.objects.exclude(last_checkin__gte=three_months_ago).filter(machine_group=machine_group)
    
    if operating_system is not None:
        machines = Machine.objects.filter(machine_group=machine_group).filter(operating_system__exact=operating_system)
    
    if req_type == 'errors':
        machines = Machine.objects.filter(errors__gt=0, machine_group=machine_group)
    
    if req_type == 'warnings':
        machines = Machine.objects.filter(warnings__gt=0, machine_group=machine_group)
    
    if req_type == 'active':
        machines = Machine.objects.filter(activity__isnull=False, machine_group=machine_group)
    
    if req_type == 'disk_space_ok':
        machines = Machine.objects.filter(hd_percent__lt=80, machine_group=machine_group)
    
    if req_type == 'disk_space_warning':
        machines = Machine.objects.filter(hd_percent__range=["80", "89"], machine_group=machine_group)
    
    if req_type == 'disk_space_alert':
        machines = Machine.objects.filter(hd_percent__gte=90, machine_group=machine_group)
    
    if req_type == 'mem_ok':
        machines = Machine.objects.filter(memory_kb__gte=mem_8_gb, machine_group=machine_group)
    
    if req_type == 'mem_warning':
        machines = Machine.objects.filter(memory_kb__range=[mem_4_gb, mem_775_gb], machine_group=machine_group)
        
    if req_type == 'mem_alert':
        machines = Machine.objects.filter(memory_kb__lt=mem_4_gb, machine_group=machine_group)
    
    if req_type == 'uptime_ok':
        machines = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__lte=1, machine_group=machine_group)
    
    if req_type == 'uptime_warning':
        machines = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__range=[1,7], machine_group=machine_group)
    
    if req_type == 'uptime_alert':
        machines = Machine.objects.filter(fact__fact_name='uptime_days', fact__fact_data__gt=7, machine_group=machine_group)
        
    if req_type == 'pending_updates':
        machines = Machine.objects.filter(pendingupdate__update=pending_update, machine_group=machine_group)
        
    if req_type == 'pending_apple_updates':
        machines = Machine.objects.filter(pendingappleupdate__update=pending_apple_update, machine_group=machine_group)

    c = {'user':user, 'machine_group': machine_group, 'business_unit': business_unit, 'machines': machines, 'req_type': req_type, 'data': data }
    return render_to_response('server/overview_list_group.html', c, context_instance=RequestContext(request))

# Machine detail
@login_required
def machine_detail(request, req_type, data, machine_id):
    # check the user is in a BU that's allowed to see this Machine
    machine = get_object_or_404(Machine, pk=machine_id)
    machine_group = machine.machine_group
    business_unit = machine_group.business_unit
    user = request.user
    user_level = user.userprofile.level
    if business_unit not in user.businessunit_set.all():
        if user_level != 'GA':
            return redirect(index)
    
    report = machine.get_report()
    if machine.fact_set.count() != 0:
        facts = machine.fact_set.all()
        if settings.EXCLUDED_FACTS:
            for excluded in settings.EXCLUDED_FACTS:
                facts = facts.exclude(fact_name=excluded)
    else:
        facts = None
    install_results = {}
    for result in report.get('InstallResults', []):
        nameAndVers = result['name'] + '-' + result['version']
        if result['status'] == 0:
            install_results[nameAndVers] = "installed"
        else:
            install_results[nameAndVers] = 'error'
    
    if install_results:         
        for item in report.get('ItemsToInstall', []):
            name = item.get('display_name', item['name'])
            nameAndVers = ('%s-%s' 
                % (name, item['version_to_install']))
            item['install_result'] = install_results.get(
                nameAndVers, 'pending')
                
        for item in report.get('ManagedInstalls', []):
            if 'version_to_install' in item:
                name = item.get('display_name', item['name'])
                nameAndVers = ('%s-%s' 
                    % (name, item['version_to_install']))
                if install_results.get(nameAndVers) == 'installed':
                    item['installed'] = True
                    
    # handle items that were removed during the most recent run
    # this is crappy. We should fix it in Munki.
    removal_results = {}
    for result in report.get('RemovalResults', []):
        m = re.search('^Removal of (.+): (.+)$', result)
        if m:
            try:
                if m.group(2) == 'SUCCESSFUL':
                    removal_results[m.group(1)] = 'removed'
                else:
                    removal_results[m.group(1)] = m.group(2)
            except IndexError:
                pass
    
    if removal_results:
        for item in report.get('ItemsToRemove', []):
            name = item.get('display_name', item['name'])
            item['install_result'] = removal_results.get(
                name, 'pending')
            if item['install_result'] == 'removed':
                if not 'RemovedItems' in report:
                    report['RemovedItems'] = [item['name']]
                elif not name in report['RemovedItems']:
                    report['RemovedItems'].append(item['name'])
                
    if 'managed_uninstalls_list' in report:
        report['managed_uninstalls_list'].sort()
    
    c = {'user':user, 'req_type': req_type, 'machine_group': machine_group, 'business_unit': business_unit, 'report': report, 'install_results': install_results, 'removal_results': removal_results, 'machine': machine, 'data': data, 'facts':facts }
    return render_to_response('server/machine_detail.html', c, context_instance=RequestContext(request))

# checkin
@csrf_exempt
def checkin(request):
    if request.method != 'POST':
        print 'not post data'
        raise Http404
    
    data = request.POST
    key = data.get('key')
    serial = data.get('serial')
    business_unit = get_object_or_404(BusinessUnit, key=key)
    if not business_unit:
        print 'no business unit'
    
    # look for serial number - if it doesn't exist, create one
    if serial:
        try:
            machine = Machine.objects.get(serial=serial)
        except Machine.DoesNotExist:
            machine = Machine(serial=serial)
    if machine:
        machine.hostname = data.get('name', '<NO NAME>').strip()
        machine.last_checkin = datetime.now()
        if 'username' in data:
            machine.username = data.get('username')
        if 'base64bz2report' in data:
            machine.update_report(data.get('base64bz2report'))
        
        # extract machine data from the report
        report_data = machine.get_report()
        # find the matching group based on manifest
        if 'ManifestName' in report_data:
            manifest = report_data['ManifestName']
            machine_group = get_object_or_404(MachineGroup, business_unit=business_unit, manifest=manifest)
            if not machine_group:
                print 'no machine group found'
            machine.machine_group = machine_group
            # print machine_group
            machine.manifest = manifest
        if 'MachineInfo' in report_data:
            machine.operating_system = report_data['MachineInfo'].get(
                'os_vers', 'UNKNOWN')
            # some machines are reporting 10.9, some 10.9.0 - make them the same
            if len(machine.operating_system) <= 4:
                machine.operating_system = machine.operating_system + '.0'
        machine.hd_space = report_data.get('AvailableDiskSpace') or 0
        machine.hd_total = int(data.get('disk_size')) or 0
        
        machine.hd_percent = int(round(((float(machine.hd_total)-float(machine.hd_space))/float(machine.hd_total))*100))
        machine.munki_version = report_data.get('ManagedInstallVersion') or 0
        hwinfo = {}
        if 'SystemProfile' in report_data.get('MachineInfo', []):
            for profile in report_data['MachineInfo']['SystemProfile']:
                if profile['_dataType'] == 'SPHardwareDataType':
                    hwinfo = profile._items[0]
                    break
        
        if hwinfo:
            machine.machine_model = hwinfo.get('machine_model')
            machine.cpu_type = hwinfo.get('cpu_type')
            machine.cpu_speed = hwinfo.get('current_processor_speed')
            machine.memory = hwinfo.get('physical_memory')

            if hwinfo.get('physical_memory')[-2:] == 'MB':
                memory_mb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_mb * 1024)
            if hwinfo.get('physical_memory')[-2:] == 'GB':
                memory_gb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_gb * 1024 * 1024)
            if hwinfo.get('physical_memory')[-2:] == 'TB':
                memory_tb = float(hwinfo.get('physical_memory')[:-3])
                machine.memory_kb = int(memory_tb * 1024 * 1024 * 1024)

        machine.save()
        
        # Remove existing PendingUpdates for the machine
        updates = machine.pendingupdate_set.all()
        updates.delete()
        if 'ItemsToInstall' in report_data:
            for update in report_data.get('ItemsToInstall'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()
        
        # Remove existing PendingAppleUpdates for the machine
        updates = machine.pendingappleupdate_set.all()
        updates.delete()
        if 'AppleUpdates' in report_data:
            for update in report_data.get('AppleUpdates'):
                display_name = update.get('display_name', update['name'])
                update_name = update.get('name')
                version = str(update['version_to_install'])
                pending_update = PendingAppleUpdate(machine=machine, display_name=display_name, update_version=version, update=update_name)
                pending_update.save()
            
        # if Facter data is submitted, we need to first remove any existing facts for this machine
        if 'Facter' in report_data:
            facts = machine.fact_set.all()
            facts.delete()
            # now we need to loop over the submitted facts and save them
            for fact_name, fact_data in report_data['Facter'].iteritems():
                fact = Fact(machine=machine, fact_name=fact_name, fact_data=fact_data)
                fact.save()
        
        return HttpResponse("Sal report submmitted for %s.\n" 
                            % data.get('name'))