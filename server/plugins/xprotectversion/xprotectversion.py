from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count, F
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
from django.conf import settings


class XprotectVersion(IPlugin):
    def widget_width(self):
        return 4

    def get_description(self):
        return 'Xprotect version'

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('xprotectversion/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('xprotectversion/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('xprotectversion/templates/id.html')

        try:
            xprotect_info = machines.filter(pluginscriptsubmission__plugin__exact='XprotectVersion', pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Version').annotate(
                xprotect_version=F('pluginscriptsubmission__pluginscriptrow__pluginscript_data')).values('xprotect_version').annotate(count=Count('xprotect_version')).order_by('xprotect_version')
        except:
            xprotect_info = []

        c = Context({
            'title': 'Xprotect Version',
            'data': xprotect_info,
            'theid': theid,
            'page': page,
            'plugin': 'XprotectVersion',
        })
        return t.render(c)

    def filter_machines(self, machines, data):
        machines = machines.filter(pluginscriptsubmission__plugin__exact='XprotectVersion',
                                   pluginscriptsubmission__pluginscriptrow__pluginscript_name__exact='Version', pluginscriptsubmission__pluginscriptrow__pluginscript_data__exact=data)

        return machines, 'Machines with Xprotect version ' + data
