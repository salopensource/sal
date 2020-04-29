from datetime import timedelta

import django.utils.timezone
from django.db.models import Q

import sal.plugin


PUPPET_Q = Q(facts__management_source__name='Puppet')

TITLES = {
    'puppeterror': 'Machines with Puppet errors',
    '1month': 'Machines that haven\'t run Puppet for more than 1 Month',
    'success': 'Machines that have run Puppet succesfully'}


class PuppetStatus(sal.plugin.Widget):

    description = 'Current status of Puppet'
    supported_os_families = [sal.plugin.OSFamilies.darwin,
                             sal.plugin.OSFamilies.linux, sal.plugin.OSFamilies.windows]

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        machines = self._get_active_machines(queryset)
        context['error_count'] = self._filter(machines, 'puppeterror').count()
        context['success_count'] = machines.count() - context['error_count']
        context['month_count'] = self._filter(machines, '1month').count()
        return context

    def filter(self, machines, data):
        try:
            title = TITLES[data]
        except KeyError:
            return None, None

        machines = self._filter(machines, data)

        return machines, title

    def _get_active_machines(self, queryset):
        """Return collection of machine ids actively puppeting."""
        return queryset.filter(
            PUPPET_Q,
            facts__fact_data__isnull=False,
            facts__fact_name='last_puppet_run')

    def _filter(self, machines, data):
        if data == 'puppeterror':
            machines = machines.filter(
                PUPPET_Q,
                facts__fact_name='puppet_errors',
                facts__fact_data__gt=0)

        elif data == '1month':
            now = django.utils.timezone.now()
            today = now - timedelta(hours=24)
            month_ago = today - timedelta(days=30)

            machines = machines.filter(
                PUPPET_Q,
                facts__fact_name='last_puppet_run',
                facts__fact_data__lte=month_ago)

        elif data == 'success':
            machines = machines.filter(
                PUPPET_Q,
                facts__fact_name='puppet_errors',
                facts__fact_data=0)

        return machines
