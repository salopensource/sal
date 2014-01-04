from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

mem_4_gb = 4 * 1024 * 1024
mem_415_gb = 4.15 * 1024 * 1024
mem_775_gb = 7.75 * 1024 * 1024
mem_8_gb = 8 * 1024 * 1024

class Memory(IPlugin):
    def show_widget(self, page, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('plugins/traffic_lights_front.html')
            machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')
            machines = utils.getBUmachines(theid)
        
        if page == 'group_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            machines = Machine.objects.filter(machine_group=machine_group)
            
        if machines:
            mem_ok = machines.filter(memory_kb__gte=mem_8_gb).count()
            mem_warning = machines.filter(memory_kb__range=[mem_4_gb, mem_775_gb]).count()
            mem_alert = machines.filter(memory_kb__lt=mem_4_gb).count()
        else:
            mem_ok = 0
            mem_warning = 0
            mem_alert = 0
        
        c = Context({
            'title': 'Memory',
            'ok_label': '8GB +',
            'ok_count': mem_ok,
            'warning_label': '4GB +',
            'warning_count': mem_warning,
            'alert_label': '> 4GB',
            'alert_count': mem_alert,
            'plugin': 'Memory',
            'theid': theid,
            'page': page
        })
        return t.render(c), 4
        
    def filter_machines(self, machines, data):
        if data == 'ok':
            machines = machines.filter(memory_kb__gte=mem_8_gb)
            title = 'Machines with more than 8GB memory'
    
        elif data == 'warning':
            machines = machines.filter(memory_kb__range=[mem_4_gb, mem_775_gb])
            title = 'Machines with more than 4GB memory'
    
        elif data == 'alert':
            machines = machines.filter(memory_kb__lt=mem_4_gb)
            title = 'Machines with less than 4GB memory'
    
        else:
            machines = None
            title = None
    
        return machines, title