from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils


class MachineDetailSecurity(IPlugin):
    def plugin_type(self):
        return 'machine_detail'

    def supported_os_families(self):
        return ['Darwin']

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Security related information'

    def widget_content(self, page, machines=None, theid=None):

        t = loader.get_template('machinedetailsecurity/templates/machinedetailsecurity.html')

        try:
            fv_status = PluginScriptRow.objects.filter(submission__machine=machines, submission__plugin__exact='MachineDetailSecurity',
                                                       pluginscript_name__exact='Filevault').order_by('submission__recorded').first()
            fv_status = fv_status.pluginscript_data
        except Exception:
            fv_status = 'Unknown'

        try:
            sip_status = PluginScriptRow.objects.filter(
                submission__machine=machines, submission__plugin__exact='MachineDetailSecurity', pluginscript_name__exact='SIP', pluginscript_data__exact='Disabled')
            if len(sip_status) != 0:
                sip_status = 'Disabled'
            else:
                sip_status = 'Enabled'
            # sip_status = sip_status.pluginscript_data
        except Exception:
            sip_status = 'Unknown'

        try:
            gatekeeper_status = PluginScriptRow.objects.filter(
                submission__machine=machines, submission__plugin__exact='MachineDetailSecurity', pluginscript_name__exact='Gatekeeper').order_by('submission__recorded').first()
            gatekeeper_status = gatekeeper_status.pluginscript_data
        except Exception:
            gatekeeper_status = 'Unknown'

        c = Context({
            'title': 'Security',
            'fv_status': fv_status,
            'sip_status': sip_status,
            'gatekeeper_status': gatekeeper_status,
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        machines = machines.filter(operating_system__exact=data)

        return machines, 'Machines running ' + data
