from yapsy.IPlugin import IPlugin

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


class Uptime(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Current uptime'

    def widget_content(self, page, machines=None, theid=None):
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

            ok = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays', pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=ok_range).count()  # noqa: E501

            warning_range = []
            for i in range(30, 90):
                warning_range.append(str(i))

            warning = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays', pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=warning_range).count()  # noqa: E501

            not_alert_range = []
            for i in range(0, 90):
                not_alert_range.append(str(i))
            alert = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays').exclude(pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=not_alert_range).count()  # noqa: E501
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
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays', pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=ok_range)  # noqa: E501
            title = 'Machines with less than 30 days of uptime'

        elif data == 'warning':
            warning_range = []
            for i in range(30, 90):
                warning_range.append(str(i))
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays', pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=warning_range)  # noqa: E501
            title = 'Machines with less than 90 days of uptime'

        elif data == 'alert':
            not_alert_range = []
            for i in range(0, 90):
                not_alert_range.append(str(i))
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Uptime', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='UptimeDays').exclude(pluginscriptsubmission__pluginscriptrow__pluginscript_data__in=not_alert_range)  # noqa: E501
            title = 'Machines with more than 90 days of uptime'

        else:
            machines = None

        return machines, title
