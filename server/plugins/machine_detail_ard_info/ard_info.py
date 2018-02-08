#!/usr/bin/python


from django.template import loader, Context
from yapsy.IPlugin import IPlugin

from server.models import PluginScriptRow


class ARDInfo(IPlugin):
    name = "ARD Info"

    def widget_width(self):
        return 4

    def plugin_type(self):
        return 'machine_detail'

    def get_description(self):
        return "Apple Remote Desktop's Computer Information Fields"

    def widget_content(self, page, machine=None, theid=None):
        template = loader.get_template(
            "machine_detail_ard_info/templates/ard_info.html")

        ard_info = {}

        for i in xrange(1, 5):
            key = 'ARD_Info_{}'.format(i)
            row = PluginScriptRow.objects.filter(
                submission__machine=machine,
                submission__plugin='ARD_Info',
                pluginscript_name=key)

            try:
                val = row.first().pluginscript_data
            except Exception:
                val = ""
            ard_info[key] = val

        c = Context({
            "title": self.get_description(),
            "data": ard_info,
            "theid": theid,
            "page": page})

        return template.render(c)
