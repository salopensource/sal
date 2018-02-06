from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.db.models import Q
from datetime import datetime, timedelta, date
import django.utils.timezone

now = django.utils.timezone.now()
hour_ago = now - timedelta(hours=1)
today = now - timedelta(hours=24)
week_ago = today - timedelta(days=7)
month_ago = today - timedelta(days=30)
three_months_ago = today - timedelta(days=90)


class PuppetStatus(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Current status of Puppet'

    def widget_content(self, page, machines=None, theid=None):
        if page == 'front':
            t = loader.get_template('puppetstatus/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('puppetstatus/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('puppetstatus/templates/id.html')

        try:
            puppet_error = machines.filter(puppet_errors__gt=0).count()
            # if there aren't any records with last checkin dates, assume puppet isn't being used
            last_checkin = machines.filter(last_puppet_run__isnull=False).count()
            if last_checkin != 0:
                checked_in_this_month = machines.filter(
                    last_puppet_run__lte=month_ago, last_checkin__gte=month_ago).count()
            else:
                checked_in_this_month = 0

            success = machines.filter(last_puppet_run__isnull=False).filter(
                puppet_errors__exact=0).count()
        except:
            puppet_error = 0
            last_checkin = 0
            checked_in_this_month = 0
            success = 0

        if last_checkin > 0:
            size = 4
        else:
            size = 0

        c = Context({
            'title': 'Puppet Status',
            'error_label': 'Errors',
            'error_count': puppet_error,
            'month_label': '+ 1 Month',
            'month_count': checked_in_this_month,
            'plugin': 'PuppetStatus',
            'last_checkin_count': last_checkin,
            'success_count': success,
            'success_label': 'Successful',
            'theid': theid,
            'page': page
        })

        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'puppeterror':
            machines = machines.filter(puppet_errors__gt=0)
            title = 'Machines with Puppet errors'
        elif data == '1month':
            machines = machines.filter(last_puppet_run__lte=month_ago)
            title = 'Machines that haven\'t run Puppet for more than 1 Month'

        elif data == 'success':
            machines = machines.filter(last_puppet_run__isnull=False).filter(puppet_errors__exact=0)
            title = 'Machines that have run Puppet succesfully'

        else:
            machines = None
            title = None

        return machines, title
