from datetime import timedelta

import django.utils.timezone
from django.db.models import Q

import sal.plugin


class Activity(sal.plugin.Widget):

    widget_width = 12
    description = 'Current Munki activity'

    def _get_q_and_title(self, data):
        now = django.utils.timezone.now()
        today = now - timedelta(hours=24)
        month_ago = today - timedelta(days=30)
        three_months_ago = today - timedelta(days=90)
        if data == 'hour':
            hour_ago = now - timedelta(hours=1)
            return Q(last_checkin__gte=hour_ago), 'Machines seen in the last hour'
        elif data == 'today':
            return Q(last_checkin__gte=today), 'Machines seen today'
        elif data == 'month':
            return (
                Q(last_checkin__range=(three_months_ago, month_ago)),
                'Machines inactive for a month')
        elif data == 'three_months':
            return Q(last_checkin__lte=three_months_ago), 'Machines inactive for over 3 months'
        else:
            return None, None

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        for key in ('hour', 'today', 'month', 'three_months'):
            filtered_machines, _ = self.filter(queryset, key)
            context[key] = filtered_machines.count()

        return context

    def filter(self, queryset, data):
        time_filter, title = self._get_q_and_title(data)
        return queryset.filter(time_filter), title
