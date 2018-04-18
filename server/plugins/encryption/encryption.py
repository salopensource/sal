from collections import OrderedDict

from django.conf import settings
from django.db.models import Q

import sal.plugin


plugin_q = Q(pluginscriptsubmission__plugin='Encryption')
# The name got changed from Filevault to FileVault. Support both.
name_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault') | \
    Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='FileVault')
enabled_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled')
disabled_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_data='Disabled')
portable_q = Q(machine_model__contains='Book')

TITLES = {
    'laptopsok': 'Laptops with encryption enabled',
    'desktopsok': 'Desktops with encryption enabled',
    'laptopsalert': 'Laptops without encryption enabled',
    'desktopsalert': 'Desktops without encryption enabled',
    'laptopsunknown': 'Laptops with Unknown encryption state',
    'desktopsunknown': 'Desktops with Unknown encryption state'}


class Encryption(sal.plugin.Widget):

    def get_context(self, queryset, **kwargs):
        context = self.super_get_context(queryset, **kwargs)

        context['show_desktops'] = getattr(settings, 'ENCRYPTION_SHOW_DESKTOPS', False)

        laptops = OrderedDict()
        laptops['ok'] = self._filter(queryset, 'laptopsok').count()
        laptops['alert'] = self._filter(queryset, 'laptopsalert').count()
        laptops['unknown'] = (
            queryset.filter(portable_q).count() - laptops['ok'] - laptops['alert'])
        context['results'] = {'Laptops': laptops}

        if context['show_desktops']:
            desktops = OrderedDict()
            desktops['ok'] = self._filter(queryset, 'desktopsok').count()
            desktops['alert'] = self._filter(queryset, 'desktopsalert').count()
            desktops['unknown'] = (
                queryset.exclude(portable_q).count() - desktops['ok'] - desktops['alert'])
            context['results']['Desktops'] = desktops
        return context

    def filter(self, machines, data):
        if data not in TITLES:
            return None, None
        machines = self._filter(machines, data)
        title = TITLES[data]
        return machines, title

    def _filter(self, machines, data):
        if data == 'laptopsok':
            machines = machines.filter(plugin_q, name_q, enabled_q).filter(portable_q)
        elif data == 'desktopsok':
            machines = machines.filter(plugin_q, name_q, enabled_q).exclude(portable_q)
        elif data == 'laptopsalert':
            machines = machines.filter(plugin_q, name_q, disabled_q).filter(portable_q)
        elif data == 'desktopsalert':
            machines = machines.filter(plugin_q, name_q, disabled_q).exclude(portable_q)
        elif data == 'laptopsunknown':
            machines = machines.exclude(plugin_q, name_q, enabled_q)\
                               .exclude(plugin_q, name_q, disabled_q).filter(portable_q)
        elif data == 'desktopsunknown':
            machines = machines.exclude(plugin_q, name_q, enabled_q)\
                               .exclude(plugin_q, name_q, disabled_q).exclude(portable_q)
        else:
            machines = None

        return machines
