from django.db.models import Count

import sal.plugin
from server.models import ManagedItem


class PendingAppleUpdates(sal.plugin.Widget):

    description = 'List of pending third party updates'
    template = 'plugins/pendingupdates.html'
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        updates = (
            ManagedItem
            .objects
            .filter(machine__in=queryset,
                    status="PENDING",
                    management_source__name='Apple Software Update')
            .values('name')
            .annotate(count=Count('name')))

        context['data'] = sorted(updates, key=lambda x: x['name'])
        return context

    def filter(self, machines, data):
        machines = machines.filter(
            manageditem__name=data,
            manageditem__status='PENDING',
            manageditem__management_source__name='Apple Software Update')
        return machines, f'Machines that need to install {data}'
