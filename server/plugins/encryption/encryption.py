from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.conf import settings


class Encryption(IPlugin):
    def widget_width(self):
        return 4

    def widget_content(self, page, machines=None, theid=None):

        try:
            show_desktops = settings.ENCRYPTION_SHOW_DESKTOPS
        except Exception:
            show_desktops = False

        if page == 'front':
            if show_desktops:
                t = loader.get_template('encryption/templates/front_desktops.html')
            else:
                t = loader.get_template('encryption/templates/front_laptops.html')

        if page == 'bu_dashboard':
            if show_desktops:
                t = loader.get_template('encryption/templates/id_desktops.html')
            else:
                t = loader.get_template('encryption/templates/id_laptops.html')

        if page == 'group_dashboard':
            if show_desktops:
                t = loader.get_template('encryption/templates/id_desktops.html')
            else:
                t = loader.get_template('encryption/templates/id_laptops.html')

        try:
            laptop_ok = machines.filter(pluginscriptsubmission__plugin='Encryption',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_name='Filevault',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled'  # noqa: E501
                                       ).filter(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            laptop_ok = 0

        try:
            desktop_ok = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                         pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                         pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                        ).exclude(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            desktop_ok = 0

        try:
            laptop_alert = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                           pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                           pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                          ).filter(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            laptop_alert = 0

        try:
            desktop_alert = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                            pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                            pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                           ).exclude(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            desktop_alert = 0

        try:
            laptop_unk = machines.exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                          pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                          pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                         ).exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                                   pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                                   pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                                  ).filter(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            laptop_unk = 0

        try:
            desktop_unk = machines.exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                           pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                           pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                          ).exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                                    pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                                    pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                                   ).exclude(machine_model__contains='Book').count()  # noqa: E501
        except Exception:
            desktop_unk = 0

        c = Context({
            'title': 'Encryption',
            'laptop_label': 'Laptops',
            'laptop_ok_count': laptop_ok,
            'laptop_alert_count': laptop_alert,
            'laptop_unknown_count': laptop_unk,
            'desktop_label': 'Desktops',
            'desktop_ok_count': desktop_ok,
            'desktop_alert_count': desktop_alert,
            'desktop_unknown_count': desktop_unk,
            'plugin': 'Encryption',
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'laptopok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                      ).filter(machine_model__contains='Book')  # noqa: E501
            title = 'Laptops with encryption enabled'

        elif data == 'desktopok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                      ).exclude(machine_model__contains='Book')  # noqa: E501
            title = 'Desktops with encryption enabled'

        elif data == 'laptopalert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                      ).filter(machine_model__contains='Book')  # noqa: E501
            title = 'Laptops without encryption enabled'

        elif data == 'desktopalert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                      ).exclude(machine_model__contains='Book')  # noqa: E501
            title = 'Desktops without encryption enabled'

        elif data == 'laptopunk':
            machines = machines.exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                       ).exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                                 pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                                 pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                                ).filter(machine_model__contains='Book')  # noqa: E501
            title = 'Laptops with Unknown encryption state'

        elif data == 'desktopunk':
            machines = machines.exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled'  # noqa: E501
                                       ).exclude(pluginscriptsubmission__plugin__exact='Encryption',  # noqa: E501
                                                 pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault',  # noqa: E501
                                                 pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled'  # noqa: E501
                                                ).exclude(machine_model__contains='Book')  # noqa: E501
            title = 'Desktops with Unknown encryption state'

        else:
            machines = None
            title = None

        return machines, title
