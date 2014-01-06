from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class Encryption(IPlugin):
    def show_widget(self, page, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('encryption/templates/front.html')
            machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            t = loader.get_template('encryption/templates/id.html')
            business_unit = get_object_or_404(BusinessUnit, pk=theid)
            machines = utils.getBUmachines(theid)
            
        if page == 'group_dashboard':
            t = loader.get_template('encryption/templates/id.html')
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            machines = Machine.objects.filter(machine_group=machine_group)
        
        if machines:
            laptop_ok = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data='true').filter(fact__fact_name='mac_laptop', fact__fact_data='mac_laptop').count()
            desktop_ok = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='true').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_desktop').count()
            laptop_alert = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='false').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_laptop').count()
            desktop_alert = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='false').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_desktop').count()
        else:
            laptop_ok = 0
            desktop_ok = 0
            laptop_alert = 0
            desktop_alert = 0

        c = Context({
            'title': 'Encryption',
            'laptop_label': 'Laptops',
            'laptop_ok_count': laptop_ok,
            'laptop_alert_count': laptop_alert,
            'desktop_ok_count': desktop_ok,
            'desktop_alert_count': desktop_alert,
            'desktop_label': 'Desktops',
            'plugin': 'Encryption',
            'theid': theid,
            'page': page
        })
        return t.render(c), 5
    
    def filter_machines(self, machines, data):
        if data == 'laptopok':
            machines = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data='true').filter(fact__fact_name='mac_laptop', fact__fact_data='mac_laptop')
            title = 'Laptops with encryption enabled'
        
        elif data == 'desktopok':
            machines = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='true').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_desktop')
            title = 'Desktops with encryption enabled'
        
        elif data == 'laptopalert':
            machines = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='false').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_laptop')
            title = 'Laptops without encryption enabled'
            
        elif data == 'desktopalert':
            machines = machines.filter(fact__fact_name='mac_encryption_enabled', fact__fact_data__exact='false').filter(fact__fact_name='mac_laptop', fact__fact_data__exact='mac_desktop')
            title = 'Desktops without encryption enabled'
        
        else:
            machines = None
            title = None
        
        return machines, title