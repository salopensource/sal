from datetime import date, datetime, timedelta

from yapsy.IPlugin import IPlugin

import django.utils.timezone
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import Context, loader

import server.utils as utils
from server.models import *


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
        if page == 'front':
            t = loader.get_template('newmachines/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('newmachines/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('newmachines/templates/id.html')

        try:
            today = machines.filter(first_checkin__gte=this_day).count()
        except Exception:
            today = 0

        try:
            this_week = machines.filter(first_checkin__gte=week_ago).count()
        except Exception:
            this_week = 0

        try:
            this_month = machines.filter(first_checkin__gte=month_ago).count()
        except Exception:
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
