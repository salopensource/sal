from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.conf import settings

class Gatekeeper(IPlugin):
    def widget_width(self):
        return 4

    def widget_content(self, page, machines=None, theid=None):


        if page == 'front':
            t = loader.get_template('gatekeeper/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('gatekeeper/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('gatekeeper/templates/id.html')


        try:
            ok = machines.filter(pluginscriptsubmission__plugin__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled').count()
        except:
            ok = 0

        try:
            alert = machines.filter(pluginscriptsubmission__plugin__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled').count()
        except:
            alert = 0

        c = Context({
            'title': 'Gatekeeper',
            'ok_count': ok,
            'alert_count': alert,
            'plugin': 'Gatekeeper',
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        if data == 'ok':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Enabled')
            title = 'Machines with Gatekeeper enabled'

        elif data == 'alert':
            machines = machines.filter(pluginscriptsubmission__plugin__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Gatekeeper', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact='Disabled')
            title = 'Machines without Gatekeeper enabled'

        else:
            machines = None
            title = None

        return machines, title
