from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class Status(IPlugin):
    def plugin_type(self):
        return 'builtin'
        
    def show_widget(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('status/templates/front.html')
            if not machines:
                machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            t = loader.get_template('status/templates/id.html')
            if not machines:
                machines = utils.getBUmachines(theid)
        
        if page == 'group_dashboard':
            t = loader.get_template('status/templates/id.html')
            if not machines:
                machine_group = get_object_or_404(MachineGroup, pk=theid)
                machines = Machine.objects.filter(machine_group=machine_group)
        
        if machines:
            errors = machines.filter(errors__gt=0).count()
            warnings = machines.filter(warnings__gt=0).count()
            activity = machines.filter(activity__isnull=False).count()
            all_machines = machines.count()
        else:
            errors = None
            warnings = None
            activity = None
            all_machines = None

        c = Context({
            'title': 'Status',
            'errors': errors,
            'warnings': warnings,
            'activity': activity,
            'all_machines': all_machines,
            'theid': theid,
            'page': page
        })
        return t.render(c), 4
    
    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.
        
        if data == 'errors':
            machines = machines.filter(errors__gt=0)
            title = 'Machines with MSU errors'
        
        if data == 'warnings':
            machines = machines.filter(warnings__gt=0)
            title = 'Machines with MSU warnings'
        
        if data == 'activity':
            machines = machines.filter(activity__isnull=False)
            title = 'Machines with MSU activity'
        
        if data == 'all_machines':
            machines = machines
            title = 'All Machines'
        
        return machines, title    