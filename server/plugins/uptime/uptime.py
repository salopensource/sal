from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils


class Uptime(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Current uptime'

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.

        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('plugins/traffic_lights_front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')

        if page == 'group_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')

        try:
            ok_range = []
            for i in range(0, 30):
                ok_range.append(str(i))

            ok = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays',
                                 pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=ok_range).count()

            warning_range = []
            for i in range(30, 90):
                warning_range.append(str(i))

            warning = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays',
                                      pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=warning_range).count()

            not_alert_range = []
            for i in range(0, 90):
                not_alert_range.append(str(i))
            alert = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays').exclude(
                pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=not_alert_range).count()
        except Exception:
            ok = 0
            warning = 0
            alert = 0

        c = Context({
            'title': 'Uptime',
            'ok_label': '< 30 Days',
            'ok_count': ok,
            'warning_label': '< 90 Days',
            'warning_count': warning,
            'alert_label': '90 Days +',
            'alert_count': alert,
            'plugin': 'Uptime',
            'page': page,
            'theid': theid
        })
        return t.render(c)

    def filter_machines(self, machines, data):

        if data == 'ok':
            ok_range = []
            for i in range(0, 30):
                ok_range.append(str(i))
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays',
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=ok_range)
            title = 'Machines with less than 30 days of uptime'

        elif data == 'warning':
            warning_range = []
            for i in range(30, 90):
                warning_range.append(str(i))
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays',
                                       pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=warning_range)
            title = 'Machines with less than 90 days of uptime'

        elif data == 'alert':
            not_alert_range = []
            for i in range(0, 90):
                not_alert_range.append(str(i))
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays').exclude(
                pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=not_alert_range)
            title = 'Machines with more than 90 days of uptime'

        else:
            machines = None

        return machines, title
