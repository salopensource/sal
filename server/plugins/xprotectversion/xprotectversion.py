from django.db.models import Count, F, Q

import sal.plugin


PLUGIN_Q = Q(pluginscriptsubmission__plugin='XprotectVersion',
             pluginscriptsubmission__pluginscriptrow__pluginscript_name='Version')


class XprotectVersion(sal.plugin.MachinesPlugin):

    description = 'Xprotect version'

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)
        context['data'] = (
            queryset
            .filter(PLUGIN_Q)
            .annotate(
                xprotect_version=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data'))
            .values('xprotect_version')
            .annotate(count=Count('xprotect_version'))
            .order_by('xprotect_version'))
        return context

    def _filter(self, machines, data):
        return machines.filter(
            PLUGIN_Q, pluginscriptsubmission__pluginscriptrow__pluginscript_data=data)

    def filter(self, machines, data):
        return self._filter(machines, data), 'Machines with Xprotect version ' + data
