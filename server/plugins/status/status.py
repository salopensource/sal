from collections import OrderedDict
from datetime import timedelta

import django.utils.timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

import sal.plugin
from server.models import Machine, MachineGroup, BusinessUnit


NOW = django.utils.timezone.now()
TODAY = NOW - timedelta(hours=24)
WEEK_AGO = TODAY - timedelta(days=7)
MONTH_AGO = TODAY - timedelta(days=30)
THREE_MONTHS_AGO = TODAY - timedelta(days=90)

# TODO: This can be cleaned up post-py3k since I believe dicts are
# ordered by default.
STATUSES = OrderedDict()
STATUSES['broken_clients'] = ('Machines with broken Python', Q(broken_client=True))
STATUSES['errors'] = ('Machines with MSU errors', Q(errors__gt=0))
STATUSES['warnings'] = ('Machines with MSU warnings', Q(warnings__gt=0))
STATUSES['activity'] = ('Machines with MSU activity', Q(activity=True))
STATUSES['sevendayactive'] = ('7 day active machines', Q(last_checkin__gte=WEEK_AGO))
STATUSES['thirtydayactive'] = ('30 day active machines', Q(last_checkin__gte=MONTH_AGO))
STATUSES['ninetydayactive'] = ('90 day active machines', Q(last_checkin__gte=THREE_MONTHS_AGO))
STATUSES['all_machines'] = ('All machines', None)
STATUSES['deployed_machines'] = ('Deployed Machines', None)
STATUSES['undeployed_machines'] = ('Undeployed Machines', Q(deployed=False))


class Status(sal.plugin.Widget):

    description = 'General status'
    only_use_deployed_machines = False

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        context['data'] = OrderedDict()
        for key, item in STATUSES.items():
            context['data'][key] = (item[0], self._filter(queryset, key).count())

        return context

    def filter(self, machines, data):
        if data not in STATUSES:
            return None, None
        machines = self._filter(machines, data)
        title = STATUSES[data][0]
        return machines, title

    def _filter(self, machines, data):
        try:
            machine_filter = STATUSES[data][1]
        except KeyError:
            return None

        # Since this plugin gets _all_ machines, we may need to filter
        # out undeployed machines depending on the type of status we're
        # checking.
        if data not in ('undeployed_machines', 'all_machines'):
            machines = machines.filter(deployed=True)

        # Only filter if a filter from the STATUSES table is defined.
        return machines.filter(machine_filter) if machine_filter else machines
