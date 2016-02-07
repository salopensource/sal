from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from datetime import datetime, timedelta, date
import django.utils.timezone

now = django.utils.timezone.now()
this_day = now - timedelta(hours=24)
week_ago = this_day - timedelta(days=7)
month_ago = this_day - timedelta(days=30)

class NewMachines(IPlugin):
    def plugin_type(self):
        return 'builtin'
    def widget_width(self):
        return 4

    def get_description(self):
        return 'New machines'

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.

        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('newmachines/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('newmachines/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('newmachines/templates/id.html')

        try:
            today = machines.filter(first_checkin__gte=this_day).count()
        except:
            today = 0

        try:
            this_week = machines.filter(first_checkin__gte=week_ago).count()
        except:
            this_week = 0

        try:
            this_month = machines.filter(first_checkin__gte=month_ago).count()
        except:
            this_month = 0

        c = Context({
            'title': 'New Machines',
            'today_label': 'Today',
            'today_count': today,
            'week_label': 'This Week',
            'week_count': this_week,
            'month_label': 'This Month',
            'month_count': this_month,
            'plugin': 'NewMachines',
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'day':
            machines = machines.filter(first_checkin__gte=this_day)
            title = 'Machines first seen today'

        elif data == 'week':
            machines = machines.filter(first_checkin__gte=week_ago)
            title = 'Machines first seen this week'

        elif data == 'month':
            machines = machines.filter(first_checkin__gte=month_ago)
            title = 'Machines first seen this month'

        else:
            machines = None

        return machines, title
