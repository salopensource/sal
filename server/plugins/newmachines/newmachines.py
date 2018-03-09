from collections import OrderedDict
from datetime import timedelta

import django.utils.timezone

import sal.plugin


TODAY = django.utils.timezone.now() - timedelta(hours=24)
RANGES = OrderedDict(Today=TODAY)
RANGES['This Week'] = TODAY - timedelta(days=7)
RANGES['This Month'] = TODAY - timedelta(days=30)


class NewMachines(sal.plugin.MachinesPlugin):

    description = 'New machines'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        data = OrderedDict()
        for key, date_range in RANGES.items():
            data[key] = queryset.filter(first_checkin__gte=date_range).count()
        context['data'] = data
        return context

    def filter(self, machines, data):
        try:
            machines = machines.filter(first_checkin__gte=RANGES[data])
        except KeyError:
            return None, None

        title = 'Machines first seen {}'.format(data.lower())

        return machines, title
