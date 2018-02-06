from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
import re


class MachineModels(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Chart of machine models'

    def widget_content(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.

        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('machinemodels/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('machinemodels/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('machinemodels/templates/id.html')

        try:
            machines = machines.filter(machine_model__isnull=False).exclude(machine_model=u'').values(
                'machine_model').annotate(count=Count('machine_model')).order_by('machine_model')
        except:
            machines = []

        output = []

        for machine in machines:
            if machine['machine_model']:
                found = False
                nodigits = ''.join(i for i in machine['machine_model'] if i.isalpha())
                machine['machine_model'] = nodigits
                for item in output:
                    if item['machine_model'] == machine['machine_model']:
                        item['count'] = item['count'] + machine['count']
                        found = True
                        break
                # if we get this far, it's not been seen before
                if found == False:
                    output.append(machine)

        c = Context({
            'title': 'Models',
            'data': output,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.

        if data == 'MacBook':
            machines = machines.filter(machine_model__startswith=data).exclude(
                machine_model__startswith='MacBookPro').exclude(machine_model__startswith='MacBookAir')
        else:
            machines = machines.filter(machine_model__startswith=data)

        title = data
        return machines, title
