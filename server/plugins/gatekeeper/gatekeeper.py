from django.db.models import Q

import sal.plugin


TITLES = {
    'ok': 'Machines with Gatekeeper enabled',
    'alert': 'Machines without Gatekeeper enabled',
    'unknown': 'Machines with unknown Gatekeeper status'}
PLUGIN_Q = Q(pluginscriptsubmission__plugin='Gatekeeper')
SCRIPT_Q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='Gatekeeper')


class Gatekeeper(sal.plugin.Widget):

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        context['ok'] = self._filter(queryset, 'ok').count()
        context['alert'] = self._filter(queryset, 'alert').count()
        context['unknown'] = queryset.count() - context['ok'] - context['alert']
        return context

    def filter(self, machines, data):
        if data not in TITLES:
            return None, None
        return self._filter(machines, data), TITLES[data]

    def _filter(self, machines, data):
        if data == 'ok':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        SCRIPT_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled'))
        elif data == 'alert':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        SCRIPT_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data='Disabled'))
        elif data == 'unknown':
            machines = (
                machines
                .exclude(pk__in=self._filter(machines, 'ok').values('pk'))
                .exclude(pk__in=self._filter(machines, 'alert').values('pk')))

        return machines
