from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class DiskSpace(IPlugin):
    def widget_width(self):
        return 4

    def plugin_type(self):
        return 'builtin'
        
    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('plugins/traffic_lights_front.html')
        
        if page == 'bu_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')
            
        if page == 'group_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')
        
        try:
            disk_ok = machines.filter(hd_percent__lt=80).count()
        except::
            disk_ok = 0

        try:
            disk_warning = machines.filter(hd_percent__range=["80", "89"]).count()
        except:
            disk_warning = 0
        
        try:
            disk_alert = machines.filter(hd_percent__gte=90).count()
        except:
            disk_alert = 0

        c = Context({
            'title': 'Disk Space',
            'ok_label': '< 80%',
            'ok_count': disk_ok,
            'warning_label': '80% +',
            'warning_count': disk_warning,
            'alert_label': '90% +',
            'alert_count': disk_alert,
            'plugin': 'DiskSpace',
            'theid': theid,
            'page': page
        })
        return t.render(c)
    
    def filter_machines(self, machines, data):
        if data == 'ok':
            machines = machines.filter(hd_percent__lt=80)
            title = 'Machines with less than 80% disk utilization'
        
        elif data == 'warning':
            machines = machines.filter(hd_percent__range=["80", "89"])
            title = 'Machines with 80%-90% disk utilization'
        
        elif data == 'alert':
            machines = machines.filter(hd_percent__gte=90)
            title = 'Machines with more than 90% disk utilization'
        
        else:
            machines = None
        
        return machines, title
