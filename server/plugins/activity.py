from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from datetime import datetime, timedelta, date

now = datetime.now()
hour_ago = now - timedelta(hours=1)
today = date.today()
week_ago = today - timedelta(days=7)
month_ago = today - timedelta(days=30)
three_months_ago = today - timedelta(days=90)
machine_data = {}

class Activity(IPlugin):
    def show_widget(self, page, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('plugins/activity/front.html')
            machines = Machine.objects.all()
        
        if page == 'bu_dashboard':
            t = loader.get_template('plugins/activity/id.html')
            machines = utils.getBUmachines(theid)
        
        if page == 'group_dashboard':
            t = loader.get_template('plugins/activity/id.html')
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            machines = Machine.objects.filter(machine_group=machine_group)
        
        if machines:
            checked_in_this_hour = machines.filter(last_checkin__gte=hour_ago).count()
            checked_in_today = machines.filter(last_checkin__gte=today).count()
            checked_in_this_week = machines.filter(last_checkin__gte=week_ago).count()
            inactive_for_a_month = machines.filter(last_checkin__range=(three_months_ago, month_ago)).count()
            inactive_for_three_months = machines.exclude(last_checkin__gte=three_months_ago).count()
        else:
            checked_in_this_hour = None
            checked_in_today = None
            checked_in_this_week = None
            inactive_for_a_month = None
            inactive_for_three_months = None

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
        return t.render(c), 4
    
    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.
        
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
        