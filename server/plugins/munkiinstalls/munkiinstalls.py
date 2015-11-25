from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from datetime import datetime, timedelta, date, time
import django.utils.timezone

this_day = django.utils.timezone.now()
two_days_ago = this_day - timedelta(days=2)
three_days_ago = this_day - timedelta(days=3)
four_days_ago = this_day - timedelta(days=4)
five_days_ago = this_day - timedelta(days=5)
six_days_ago = this_day - timedelta(days=6)
seven_days_ago = this_day - timedelta(days=7)
eight_days_ago = this_day - timedelta(days=8)
nine_days_ago = this_day - timedelta(days=9)
ten_days_ago = this_day - timedelta(days=10)
eleven_days_ago = this_day - timedelta(days=11)
twelve_days_ago = this_day - timedelta(days=12)
thirteen_days_ago = this_day - timedelta(days=13)
fourteen_days_ago = this_day - timedelta(days=14)

class MunkiInstalls(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 8

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.

        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('munkiinstalls/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('munkiinstalls/templates/front.html')

        if page == 'group_dashboard':
            t = loader.get_template('munkiinstalls/templates/front.html')

        data = []
        for time_range in [this_day, two_days_ago, three_days_ago, four_days_ago,
        five_days_ago, six_days_ago, seven_days_ago, eight_days_ago, nine_days_ago,
        ten_days_ago, eleven_days_ago, twelve_days_ago, thirteen_days_ago, fourteen_days_ago]:
            my_dict = {}
            the_min = datetime.combine(time_range, time.min)
            the_max = datetime.combine(time_range, time.max)

            installs = UpdateHistoryItem.objects.filter(status__iexact='install', recorded__range=(the_min, the_max),
            update_history__machine=machines, update_history__update_type='third_party').count()

            errors = UpdateHistoryItem.objects.filter(status='error', recorded__range=(the_min, the_max),
            update_history__machine=machines, update_history__update_type='third_party').count()

            pending = UpdateHistoryItem.objects.filter(status='pending', update_history__machine=machines, recorded__range=(the_min, the_max), update_history__update_type='third_party').count()

            my_dict['installs'] = installs
            my_dict['pending'] = pending
            my_dict['errors'] = errors
            my_dict['date'] = time_range.strftime("%Y-%m-%d")
            data.append(my_dict)

        c = Context({
            'title': 'Munki Installs',
            'data': data,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        machines = machines.filter(munki_version__exact=data)

        title = 'Machines running version '+data+' of MSC'
        return machines, title
