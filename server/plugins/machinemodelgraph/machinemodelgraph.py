from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class MachineModelGraph(IPlugin):
    def show_widget(self, page, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # we're not linking anywhere, so the template will be the same for all
        t = loader.get_template('machinemodelgraph/templates/front.html')
        if page == 'front':
            machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            machines = utils.getBUmachines(theid)
        
        if page == 'group_dashboard':
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            machines = Machine.objects.filter(machine_group=machine_group)
        
        if machines:
            machines = machines.values('machine_model').annotate(count=Count('machine_model'))
        else:
            machines = None
        
        print machines

        c = Context({
            'title': 'Hardware models',
            'machines': machines,
            'theid': theid,
            'page': page
        })
        return t.render(c), 4
    
    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.
        
        machines = machines.filter(operating_system__exact=data)
        
        return machines, 'Machines running '+data
        