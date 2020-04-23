from collections import OrderedDict
from datetime import timedelta

import django.utils.timezone

import sal.plugin


class NewMachines(sal.plugin.Widget):

    description = 'New machines'

    def _get_range(self):
        today = django.utils.timezone.now() - timedelta(hours=24)
        ranges = OrderedDict(Today=today)
        ranges['This Week'] = today - timedelta(days=7)
        ranges['This Month'] = today - timedelta(days=30)
        return ranges


    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        data = OrderedDict()
        for key, date_range in self._get_range().items():
            data[key] = queryset.filter(first_checkin__gte=date_range).count()
        context['data'] = data
        return context

    def filter(self, machines, data):
        try:
            machines = machines.filter(first_checkin__gte=self._get_range()[data])
        except KeyError:
            return None, None

        title = 'Machines first seen {}'.format(data.lower())

        return machines, title
