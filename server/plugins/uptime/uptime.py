from django.db.models import Q

import sal.plugin


# Build some Q objects for use later.
ALERT_RANGE = list(xrange(0, 90))
DATA = 'pluginscriptsubmission__pluginscriptrow__pluginscript_data__in={}'
ALERT_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE)))
OK_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE[0:30])))
WARNING_Q = eval('Q({})'.format(DATA.format(ALERT_RANGE[30:60])))

PLUGIN_Q = Q(pluginscriptsubmission__plugin='Uptime',
             pluginscriptsubmission__pluginscriptrow__pluginscript_name='UptimeDays')
TITLES = {
    'ok': 'Machines with less than 30 days of uptime',
    'warning': 'Machines with less than 90 days of uptime',
    'alert': 'Machines with more than 90 days of uptime'}


class Uptime(sal.plugin.Widget):

    description = 'Current uptime'
    template = 'plugins/traffic_lights.html'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        context['ok_count'] = self._filter(queryset, 'ok').count()
        context['warning_count'] = self._filter(queryset, 'warning').count()
        context['alert_count'] = self._filter(queryset, 'alert').count()
        context.update({
            'ok_label': '< 30 Days',
            'warning_label': '< 90 Days',
            'alert_label': '90 Days +',
        })
        return context

    def _filter(self, queryset, data):
        if data == 'ok':
            queryset = queryset.filter(PLUGIN_Q, OK_Q)
        elif data == 'warning':
            queryset = queryset.filter(PLUGIN_Q, WARNING_Q)
        elif data == 'alert':
            queryset = queryset.filter(PLUGIN_Q).exclude(ALERT_Q)
        return queryset

    def filter(self, machines, data):
        try:
            title = TITLES[data]
        except KeyError:
            return None, None

        machines = self._filter(machines, data)

        return machines, title
