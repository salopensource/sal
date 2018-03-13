from django.db.models import Q

import sal.plugin


SIP_Q = Q(pluginscriptsubmission__plugin='Sip',
          pluginscriptsubmission__pluginscriptrow__pluginscript_name='SIP')
TITLES = {'ok': 'Machines with Sip enabled',
          'alert': 'Machines without SIP enabled',
          'unknown': 'Machines with unknown SIP status.'}


class Sip(sal.plugin.Widget):

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        context['ok_count'] = (
            queryset
            .filter(SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled')
            .count())
        context['alert_count'] = (
            queryset
            .filter(SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data='Disabled')
            .count())
        context['unknown_count'] = (
            queryset
            .filter(SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data__isnull=True)
            .count())
        return context

    def filter(self, machines, data):
        try:
            title = TITLES[data]
        except KeyError:
            return None, None

        machines = self._filter(machines, data)
        return machines, title

    def _filter(self, machines, data):
        if data == 'ok':
            return machines.filter(
                SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled')
        elif data == 'alert':
            return machines.filter(
                SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data='Disabled')
        elif data == 'unknown':
            return machines.filter(
                SIP_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data__isnull=True)

        return machines
