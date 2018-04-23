from datetime import timedelta

import django.utils.timezone

import sal.plugin


NOW = django.utils.timezone.now()
TODAY = NOW - timedelta(hours=24)
MONTH_AGO = TODAY - timedelta(days=30)

TITLES = {
    'puppeterror': 'Machines with Puppet errors',
    '1month': 'Machines that haven\'t run Puppet for more than 1 Month',
    'success': 'Machines that have run Puppet succesfully'}


class PuppetStatus(sal.plugin.Widget):

    description = 'Current status of Puppet'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        context['error_count'] = self._filter(queryset, 'puppeterror').count()

        # if there aren't any records with last checkin dates, assume
        # puppet isn't being used
        # TODO: (sheagcraig) I don't understand why this is different
        # below in the filter code. Need to research with @grahamgilbert.
        last_checkin = queryset.filter(last_puppet_run__isnull=False).count()
        if last_checkin != 0:
            checked_in_this_month = queryset.filter(
                last_puppet_run__lte=MONTH_AGO, last_checkin__gte=MONTH_AGO).count()
        else:
            checked_in_this_month = 0

        context['month_count'] = checked_in_this_month
        context['success_count'] = self._filter(queryset, 'success').count()

        return context

    def filter(self, machines, data):
        try:
            title = TITLES[data]
        except KeyError:
            return None, None

        machines = self._filter(machines, data)

        return machines, title

    def _filter(self, machines, data):
        if data == 'puppeterror':
            machines = machines.filter(puppet_errors__gt=0)
        elif data == '1month':
            machines = machines.filter(last_puppet_run__lte=MONTH_AGO)
        elif data == 'success':
            machines = machines.filter(last_puppet_run__isnull=False).filter(puppet_errors__exact=0)

        return machines
