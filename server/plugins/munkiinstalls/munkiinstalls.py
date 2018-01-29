from datetime import datetime, timedelta, date, time
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template import loader
from server.models import *
from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
import django.utils.timezone
import server.utils as utils


now = django.utils.timezone.now()
this_day = now - timedelta(days=0)
one_day_ago = now - timedelta(days=1)
two_days_ago = now - timedelta(days=2)
three_days_ago = now - timedelta(days=3)
four_days_ago = now - timedelta(days=4)
five_days_ago = now - timedelta(days=5)
six_days_ago = now - timedelta(days=6)
seven_days_ago = now - timedelta(days=7)
eight_days_ago = now - timedelta(days=8)
nine_days_ago = now - timedelta(days=9)
ten_days_ago = now - timedelta(days=10)
eleven_days_ago = now - timedelta(days=11)
twelve_days_ago = now - timedelta(days=12)
thirteen_days_ago = now - timedelta(days=13)
fourteen_days_ago = now - timedelta(days=14)


class MunkiInstalls(IPlugin):

    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 8

    def get_description(self):
        return 'Chart of Munki install activity'

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a
        # template.

        # There are three possible views we're going to be rendering to -
        # front, bu_dashbaord and group_dashboard. If page is set to
        # bu_dashboard, or group_dashboard, you will be passed a
        # business_unit or machine_group id to use (mainly for linking to
        # the right search).
        if page == 'front':
            t = loader.get_template('munkiinstalls/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('munkiinstalls/templates/front.html')

        if page == 'group_dashboard':
            t = loader.get_template('munkiinstalls/templates/front.html')

        data = []
        time_ranges = [
            this_day, one_day_ago, two_days_ago, three_days_ago, four_days_ago,
            five_days_ago, six_days_ago, seven_days_ago, eight_days_ago,
            nine_days_ago, ten_days_ago, eleven_days_ago, twelve_days_ago,
            thirteen_days_ago, fourteen_days_ago]

        for time_range in time_ranges:
            my_dict = {}
            the_min = datetime.combine(time_range, time.min)
            the_max = datetime.combine(time_range, time.max)

            try:
                installs = UpdateHistoryItem.objects.filter(
                    status__iexact='install', recorded__range=(the_min, the_max),
                    update_history__machine__in=machines,
                    update_history__update_type='third_party').count()
            except Exception:
                installs = 0

            try:
                errors = UpdateHistoryItem.objects.filter(
                    status='error', recorded__range=(the_min, the_max),
                    update_history__machine__in=machines,
                    update_history__update_type='third_party').count()
            except Exception:
                errors = 0

            try:
                pending = UpdateHistoryItem.objects.filter(
                    status='pending', update_history__machine__in=machines,
                    recorded__range=(the_min, the_max),
                    update_history__update_type='third_party').count()
            except Exception:
                pending = 0

            my_dict['installs'] = installs
            my_dict['pending'] = pending
            my_dict['errors'] = errors
            my_dict['date'] = time_range.strftime("%Y-%m-%d")
            data.append(my_dict)

        c = {
            'title': 'Munki Installs',
            'data': data,
            'theid': theid,
            'page': page
        }
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to
        # perform some filtering based on the 'data' part of the url from
        # the show_widget output. Just return your filtered list of
        # machines and the page title.

        machines = machines.filter(munki_version__exact=data)

        title = 'Machines running version {} of MSC'.format(data)
        return machines, title
