from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class Uptime(IPlugin):
    def plugin_type(self):
        return 'facter'

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
            ok = machines.filter(facts__fact_name='uptime_days', facts__fact_data__lte=1).count()
            warning = machines.filter(facts__fact_name='uptime_days', facts__fact_data__range=[1,7]).count()
            alert = machines.filter(facts__fact_name='uptime_days', facts__fact_data__gt=7).count()
        except:
            ok = 0
            warning = 0
            alert = 0

        c = Context({
            'title': 'Uptime',
            'ok_label': '< 1 Day',
            'ok_count': ok,
            'warning_label': '< 7 Days',
            'warning_count': warning,
            'alert_label': '7 Days +',
            'alert_count': alert,
            'plugin': 'Uptime',
            'page': page,
            'theid': theid
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'ok':
            machines = machines.filter(facts__fact_name='uptime_days', facts__fact_data__lte=1)
            title = 'Machines with less than 1 day of uptime'

        elif data == 'warning':
            machines = machines.filter(facts__fact_name='uptime_days', facts__fact_data__range=[1,7])
            title = 'Machines with less than 1 week of uptime'

        elif data == 'alert':
            machines = machines.filter(facts__fact_name='uptime_days', facts__fact_data__gt=7)
            title = 'Machines with more than a week of uptime'

        else:
            machines = None

        return machines, title
