from server.models import PluginScriptRow

import sal.plugin


class ARDInfo(sal.plugin.DetailPlugin):

    description = "Apple Remote Desktop's Computer Information Fields"

    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, machine, **kwargs):
        context = self.super_get_context(machine, **kwargs)

        ard_info = {}
        for i in range(1, 5):
            key = 'ARD_Info_{}'.format(i)
            row = PluginScriptRow.objects.filter(
                submission__machine=machine,
                submission__plugin='ARD_Info',
                pluginscript_name=key)

            try:
                val = row.first().pluginscript_data
            except AttributeError:
                val = ""
            ard_info[key] = val

        context['data'] = ard_info

        return context
