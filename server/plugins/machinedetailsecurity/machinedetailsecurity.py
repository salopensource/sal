import sal.plugin
from server.models import PluginScriptRow


class MachineDetailSecurity(sal.plugin.DetailPlugin):

    description = 'Security related information'

    def get_context(self, machine, **kwargs):
        context = self.super_get_context(machine, **kwargs)

        try:
            fv_status = (
                PluginScriptRow.objects
                .filter(submission__machine=machine,
                        submission__plugin='MachineDetailSecurity',
                        pluginscript_name='Filevault')
                .order_by('submission__recorded')
                .first().pluginscript_data)
        except AttributeError:
            fv_status = 'Unknown'

        try:
            sip_status_count = (
                PluginScriptRow.objects
                .filter(submission__machine=machine,
                        submission__plugin='MachineDetailSecurity',
                        pluginscript_name='SIP',
                        pluginscript_data='Disabled').count())
            sip_status = 'Disabled' if sip_status_count != 0 else 'Enabled'
        except AttributeError:
            sip_status = 'Unknown'

        try:
            gatekeeper_status = (
                PluginScriptRow.objects
                .filter(submission__machine=machine,
                        submission__plugin='MachineDetailSecurity',
                        pluginscript_name='Gatekeeper')
                .order_by('submission__recorded')
                .first().pluginscript_data)
        except AttributeError:
            gatekeeper_status = 'Unknown'

        context['fv_status'] = fv_status
        context['sip_status'] = sip_status
        context['gatekeeper_status'] = gatekeeper_status
        return context

    def filter(self, machines, data):
        machines = machines.filter(operating_system=data)
        return machines, 'Machines running ' + data
