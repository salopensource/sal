from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils


class PendingAppleUpdates(IPlugin):

    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'List of pending Apple updates'

    def widget_content(self, page, machines=None, id=None):

        if page == 'front':
            t = loader.get_template('plugins/pendingupdates/front.html')
            updates = PendingAppleUpdate.objects.all()

        if page == 'bu_dashboard':
            t = loader.get_template('plugins/pendingupdates/id.html')
            business_unit = get_object_or_404(BusinessUnit, pk=id)
            updates = PendingAppleUpdate.objects.filter(
                machine__machine_group__business_unit=business_unit)

        if page == 'group_dashboard':
            t = loader.get_template('plugins/pendingupdates/id.html')
            machine_group = get_object_or_404(MachineGroup, pk=id)
            updates = PendingAppleUpdate.objects.filter(
                machine__machine_group=machine_group)

        updates = updates.values('update', 'update_version', 'display_name').annotate(
            count=Count('update')).order_by('display_name')
        pending_updates = []
        for item in updates:
            # loop over existing items, see if there is a dict with the right
            # value
            found = False
            for update in pending_updates:
                if (update['update'] == item['update'] and
                        update['update_version'] == item['update_version']):
                    update['count'] = update['count'] + item['count']
                    found = True
                    break
            if found is False:
                pending_updates.append(item)

        c = {
            'title': 'Pending Apple Updates',
            'data': pending_updates,
            'theid': id,
            'page': page,
            'plugin': 'PendingAppleUpdates'
        }

        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform
        # some filtering based on the 'data' part of the url from the
        # show_widget output. Just return your filtered list of machines and
        # the page title.

        (update_name, update_version) = data.split("--")
        machines = machines.filter(pending_apple_updates__update=update_name,
                                   pending_apple_updates__update_version=update_version)

        # get the display name of the update

        display_name = PendingAppleUpdate.objects.filter(
            update=update_name, update_version=update_version).values('display_name')

        for item in display_name:
            display_name = item['display_name']
            break

        return machines, 'Machines that need to install ' + display_name + ' ' + update_version
