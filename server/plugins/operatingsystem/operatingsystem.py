from distutils.version import LooseVersion

from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class OperatingSystem(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'List of operating system versions'

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.

        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('operatingsystem/templates/os_front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('operatingsystem/templates/os_id.html')

        if page == 'group_dashboard':
            t = loader.get_template('operatingsystem/templates/os_id.html')

        # Remove invalid versions, then count and sort the results.
        os_info = machines.exclude(
            operating_system__isnull=True).exclude(
                operating_system__exact='').values(
                'operating_system', 'os_family').annotate(
                    count=Count('operating_system')).order_by(
                        'os_family', 'operating_system')

        mac_os_info = []
        windows_os_info = []
        linux_os_info = []

        for machine in os_info:
            if machine['os_family'] == 'Darwin':
                mac_os_info.append(machine)
            elif machine['os_family'] == 'Windows':
                windows_os_info.append(machine)
            elif machine['os_family'] == 'Linux':
                linux_os_info.append(machine)

        mac_os_info = sorted(
            mac_os_info,
            key=lambda x: LooseVersion(x["operating_system"]),
            reverse=True)

        windows_os_info = sorted(
            windows_os_info,
            key=lambda x: LooseVersion(x["operating_system"]),
            reverse=True) 

        linux_os_info = sorted(
            linux_os_info,
            key=lambda x: LooseVersion(x["operating_system"]),
            reverse=True)       

        c = Context({
            'title': 'Operating Systems',
            'mac_data': mac_os_info,
            'windows_data': windows_os_info,
            'linux_data': linux_os_info,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform
        # some filtering based on the 'data' part of the url from the
        # show_widget output. Just return your filtered list of machines and
        # the page title.

        machines = machines.filter(operating_system__exact=data)

        return machines, 'Machines running '+data
