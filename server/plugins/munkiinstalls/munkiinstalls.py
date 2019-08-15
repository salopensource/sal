from datetime import datetime, time, timedelta

from django.utils import timezone

import sal.plugin
from server.models import ManagedItemHistory


NOW = timezone.now()
STATUSES = ('present', 'pending', 'error')


class MunkiInstalls(sal.plugin.Widget):

    description = 'Chart of Munki install activity'
    widget_width = 8
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        # Set up 14 days back of time ranges as a generator.
        days = (NOW - timedelta(days=d) for d in range(0, 15))
        time_ranges = ((
            timezone.make_aware(datetime.combine(d, time.min)),
            timezone.make_aware(datetime.combine(d, time.max))) for d in days)

        # For each day, get a count of installs, pending, and errors,
        # and the date, as a list of dicts.
        context['data'] = []
        for time_range in time_ranges:
            day_status = {key: self._filter(queryset, key, time_range) for key in STATUSES}
            day_status['date'] = time_range[0].strftime("%Y-%m-%d")
            context['data'].append(day_status)
        return context

    def _filter(self, queryset, data, time_range):
        return (
            ManagedItemHistory.objects
            .filter(
                status__iexact=data,
                recorded__range=time_range,
                machine__in=queryset,
                management_source__name='Munki')
            .count())
