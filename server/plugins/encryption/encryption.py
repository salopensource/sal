from yapsy.IPlugin import IPlugin

from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


plugin_q = Q(pluginscriptsubmission__plugin='Encryption')
name_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='Filevault')
enabled_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled')
disabled_q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_data='Disabled')
portable_q = Q(machine_model__contains='Book')


class Encryption(IPlugin):

    def widget_width(self):
        return 4

    def widget_content(self, page, machines=None, theid=None):
        show_desktops = getattr(settings, 'ENCRYPTION_SHOW_DESKTOPS', False)
        template_page = page if page == 'front' else 'id'
        machine_type = 'desktops' if show_desktops else 'laptops'
        template = loader.get_template(
            'encryption/templates/{}_{}.html'.format(template_page, machine_type))

        laptops = machines.filter(portable_q)
        desktops = machines.exclude(portable_q)

        laptop_ok = laptops.filter(plugin_q, name_q, enabled_q).count()
        desktop_ok = desktops.filter(plugin_q, name_q, enabled_q).count()

        laptop_alert = laptops.filter(plugin_q, name_q, disabled_q).count()
        desktop_alert = desktops.filter(plugin_q, name_q, disabled_q).count()

        laptop_unknown = laptops.count() - laptop_ok - laptop_alert
        desktop_unknown = desktops.count() - desktop_ok - desktop_alert

        context = {
            'title': 'Encryption',
            'laptop_label': 'Laptops',
            'laptop_ok_count': laptop_ok,
            'laptop_alert_count': laptop_alert,
            'laptop_unknown_count': laptop_unknown,
            'desktop_label': 'Desktops',
            'desktop_ok_count': desktop_ok,
            'desktop_alert_count': desktop_alert,
            'desktop_unknown_count': desktop_unknown,
            'plugin': 'Encryption',
            'theid': theid,
            'page': page
        }
        return template.render(context)

    def filter_machines(self, machines, data):
        if data == 'laptopok':
            machines = machines.filter(plugin_q, name_q, enabled_q).filter(portable_q)
            title = 'Laptops with encryption enabled'

        elif data == 'desktopok':
            machines = machines.filter(plugin_q, name_q, enabled_q).exclude(portable_q)
            title = 'Desktops with encryption enabled'

        elif data == 'laptopalert':
            machines = machines.filter(plugin_q, name_q, disabled_q).filter(portable_q)
            title = 'Laptops without encryption enabled'

        elif data == 'desktopalert':
            machines = machines.filter(plugin_q, name_q, disabled_q).exclude(portable_q)
            title = 'Desktops without encryption enabled'

        elif data == 'laptopunk':
            machines = machines.exclude(plugin_q, name_q, enabled_q)\
                               .exclude(plugin_q, name_q, disabled_q).filter(portable_q)
            title = 'Laptops with Unknown encryption state'

        elif data == 'desktopunk':
            machines = machines.exclude(plugin_q, name_q, enabled_q)\
                               .exclude(plugin_q, name_q, disabled_q).exclude(portable_q)
            title = 'Desktops with Unknown encryption state'

        else:
            machines = None
            title = None

        return machines, title
