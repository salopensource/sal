from datetime import timedelta

import django.utils.timezone
from django.db.models import Q

import sal.plugin


NOW = django.utils.timezone.now()
HOUR_AGO = NOW - timedelta(hours=1)
TODAY = NOW - timedelta(hours=24)
MONTH_AGO = TODAY - timedelta(days=30)
THREE_MONTHS_AGO = TODAY - timedelta(days=90)

FILTERS_AND_TITLES = {
    'hour': (Q(last_checkin__gte=HOUR_AGO), 'Machines seen in the last hour'),
    'today': (Q(last_checkin__gte=TODAY), 'Machines seen today'),
    'month': (Q(last_checkin__range=(THREE_MONTHS_AGO, MONTH_AGO)),
              'Machines inactive for a month'),
    'three_months': (Q(last_checkin__gte=THREE_MONTHS_AGO), 'Machines inactive for over 3 months')}


class Activity(sal.plugin.MachinesPlugin):

    widget_width = 12
    description = 'Current Munki activity'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        for key in FILTERS_AND_TITLES:
            filtered_machines, _ = self.filter(queryset, key)
            context[key] = filtered_machines.count()

        return context

    def filter(self, queryset, data):
        try:
            time_filter, title = FILTERS_AND_TITLES[data]
        except KeyError
            return None, None
        return queryset.filter(time_filter), title
