from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class PendingAppleUpdates(IPlugin):
    def plugin_type(self):
        return 'builtin'
        
    def show_widget(self, page, machines=None, id=None):

        if page == 'front':
            t = loader.get_template('plugins/pendingupdates/front.html')
            updates = PendingAppleUpdate.objects.all()

        if page == 'bu_dashboard':
            t = loader.get_template('plugins/pendingupdates/id.html')
            business_unit = get_object_or_404(BusinessUnit, pk=id)
            updates = PendingAppleUpdate.objects.filter(machine__machine_group__business_unit=business_unit)

        if page == 'group_dashboard':
            t = loader.get_template('plugins/pendingupdates/id.html')
            machine_group = get_object_or_404(MachineGroup, pk=id)
            updates = PendingAppleUpdate.objects.filter(machine__machine_group=machine_group)

        updates = updates.values('update', 'update_version', 'display_name').annotate(count=Count('update'))
        pending_updates = []
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

        c = Context({
            'title': 'Pending Apple Updates',
            'data': pending_updates,
            'theid': id,
            'page': page,
            'plugin': 'PendingAppleUpdates'
        })

        if len(pending_updates)==0:
            size = 0
        else:
            size = 4
        return t.render(c), size

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        machines = machines.filter(pending_apple_updates__update=data)

        # get the display name of the update

        display_name = PendingAppleUpdate.objects.filter(update=data).values('display_name')

        for item in display_name:
            display_name = item['display_name']
            break

        return machines, 'Machines that need to install '+display_name
