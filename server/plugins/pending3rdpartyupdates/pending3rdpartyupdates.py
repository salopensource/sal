import collections
from distutils.version import LooseVersion
from operator import itemgetter

import sal.plugin
from server.models import UpdateHistoryItem


class Pending3rdPartyUpdates(sal.plugin.Widget):

    description = 'List of pending third party updates'
    template = 'plugins/pendingupdates.html'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        update_items = (
            UpdateHistoryItem.objects
            .filter(
                update_history__machine__in=queryset, status='pending',
                update_history__update_type='third_party')
            .values_list('update_history__version', 'update_history__name'))
        # This is where the time really takes place.
        updates = collections.Counter(update_items)
        # TODO: Python 3.5+ version!
        # counted = (*update, count=count) for update, count in updates.items())
        counted = (update + (count, ) for update, count in updates.items())

        # Sort first by version number, then name.
        updates = sorted(counted, key=lambda x: LooseVersion(x[0]), reverse=True)
        context['data'] = sorted(updates, key=itemgetter(1))
        return context

    def filter(self, machines, data):
        try:
            (update_name, update_version) = data.split("--")
        except ValueError:
            return None, None

        involved = (
            UpdateHistoryItem.objects
            .filter(
                update_history__update_type='third_party',
                update_history__name=update_name,
                update_history__version=update_version,
                status='pending')
            .values('update_history__machine__id'))
        machines = machines.filter(id__in=involved)

        return machines, 'Machines that need to install {} {}'.format(update_name, update_version)
