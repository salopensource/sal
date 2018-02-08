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
hour_ago = now - timedelta(hours=1)
today = now - timedelta(hours=24)
week_ago = today - timedelta(days=7)
month_ago = today - timedelta(days=30)
three_months_ago = today - timedelta(days=90)
machine_data = {}


class Activity(IPlugin):
    def widget_width(self):
        return 12

    def plugin_type(self):
        return 'builtin'

    def get_description(self):
        return 'Current Munki activity'

    def widget_content(self, page, machines=None, theid=None):
        if page == 'front':
            t = loader.get_template('activity/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('activity/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('activity/templates/id.html')

        try:
            checked_in_this_hour = machines.filter(last_checkin__gte=hour_ago).count()
        except Exception:
            checked_in_this_hour = 0

        try:
            checked_in_today = machines.filter(last_checkin__gte=today).count()
        except Exception:
            checked_in_today = 0

        try:
            checked_in_this_week = machines.filter(last_checkin__gte=week_ago).count()
        except Exception:
            checked_in_this_week = 0

        try:
            inactive_for_a_month = machines.filter(
                last_checkin__range=(three_months_ago, month_ago)).count()
        except Exception:
            inactive_for_a_month = 0

        try:
            inactive_for_three_months = machines.exclude(last_checkin__gte=three_months_ago).count()
        except Exception:
            inactive_for_three_months = 0

        c = Context({
            'title': 'Activity',
            'checked_in_this_hour': checked_in_this_hour,
            'checked_in_today': checked_in_today,
            'checked_in_this_week': checked_in_this_week,
            'inactive_for_a_month': inactive_for_a_month,
            'inactive_for_three_months': inactive_for_three_months,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):

        if data == '1-hour':
            machines = machines.filter(last_checkin__gte=hour_ago)
            title = 'Machines seen in the last hour'

        if data == 'today':
            machines = machines.filter(last_checkin__gte=today)
            title = 'Machines seen today'

        if data == '1-week':
            machines = machines.filter(last_checkin__gte=week_ago)
            title = 'Machines seen in the last week'

        if data == '1-month':
            machines = machines.filter(last_checkin__range=(three_months_ago, month_ago))
            title = 'Machines inactive for a month'

        if data == '3-months':
            machines = machines.exclude(last_checkin__gte=three_months_ago)
            title = 'Machines inactive for over 3 months'

        return machines, title
