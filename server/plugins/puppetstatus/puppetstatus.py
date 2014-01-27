from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.db.models import Q
from datetime import datetime, timedelta, date

now = datetime.now()
hour_ago = now - timedelta(hours=1)
today = date.today()
week_ago = today - timedelta(days=7)
month_ago = today - timedelta(days=30)
three_months_ago = today - timedelta(days=90)


class PuppetStatus(IPlugin):
    def show_widget(self, page, machines=None, theid=None):
        if page == 'front':
            t = loader.get_template('puppetstatus/templates/front.html')
            if not machines:
                machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            t = loader.get_template('puppetstatus/templates/id.html')
            if not machines:
                machines = utils.getBUmachines(theid)
            
        if page == 'group_dashboard':
            t = loader.get_template('puppetstatus/templates/id.html')
            if not machines:
                machine_group = get_object_or_404(MachineGroup, pk=theid)
                machines = Machine.objects.filter(machine_group=machine_group)
        
        if machines:
            puppet_error = machines.filter(puppet_errors__gt=0).count()
        else:
            puppet_error = 0
        
        # if there aren't any records with last checkin dates, assume puppet isn't being used
        last_checkin = machines.filter(last_puppet_run__isnull=False).count()
        print last_checkin
        checked_in_this_week = machines.filter(last_puppet_run__lte=week_ago).count()
        
        if last_checkin > 0:
            size = 2
        else:
            size = 0
        
        c = Context({
            'title': 'Puppet Status',
            'error_label': 'Errors',
            'error_count': puppet_error,
            'week_label': '+ 7 Days',
            'week_count': checked_in_this_week,
            'plugin': 'PuppetStatus',
            'last_checkin_count': last_checkin,
            'theid': theid,
            'page': page
        })
        

        return t.render(c), size
    
    def filter_machines(self, machines, data):
        if data == 'puppeterror':
            machines = machines.filter(puppet_errors__gt=0)
            title = 'Machines with Puppet errors'
        elif data =='7days':
            machines = machines.filter(last_puppet_run__lte=week_ago)
            title = 'Machines that haven\'t run Puppet for more than 7 Days'
        
        else:
            machines = None
            title = None
        
        return machines, title