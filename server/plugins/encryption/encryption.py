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
        except:
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
            laptop_ok = machines.filter(pluginscriptsubmission__plugin='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data='Enabled').filter(machine_model__contains='Book').count()
        except:
            laptop_ok = 0

        try:
            desktop_ok = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled').exclude(machine_model__contains='Book').count()
        except:
            desktop_ok = 0

        try:
            laptop_alert = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').filter(machine_model__contains='Book').count()
        except:
            laptop_alert = 0

        try:
            desktop_alert = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').exclude(machine_model__contains='Book').count()
        except:
            desktop_alert = 0

        c = Context({
            'title': 'Encryption',
            'laptop_label': 'Laptops',
            'laptop_ok_count': laptop_ok,
            'laptop_alert_count': laptop_alert,
            'desktop_ok_count': desktop_ok,
            'desktop_alert_count': desktop_alert,
            'desktop_label': 'Desktops',
            'plugin': 'Encryption',
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'laptopok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled').filter(machine_model__contains='Book')
            title = 'Laptops with encryption enabled'

        elif data == 'desktopok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled').exclude(machine_model__contains='Book')
            title = 'Desktops with encryption enabled'

        elif data == 'laptopalert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').filter(machine_model__contains='Book')
            title = 'Laptops without encryption enabled'

        elif data == 'desktopalert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Encryption', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Filevault', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').exclude(machine_model__contains='Book')
            title = 'Desktops without encryption enabled'

        else:
            machines = None
            title = None

        return machines, title
