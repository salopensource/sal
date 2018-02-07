from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils


class SalScriptsVersion(IPlugin):
    def plugin_type(self):
        return 'builtin'

    def widget_width(self):
        return 4

    def get_description(self):
        return 'Chart of installed versions of the Sal Scripts'

    def widget_content(self, page, machines=None, theid=None):
        if page == 'front':
            t = loader.get_template('salscriptsversion/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('salscriptsversion/templates/id.html')

        if page == 'group_dashboard':
            t = loader.get_template('salscriptsversion/templates/id.html')

        try:
            sal_info = machines.values('sal_version').exclude(sal_version__isnull=True).annotate(
                count=Count('sal_version')).order_by('sal_version')
        except Exception:
            sal_info = []

        c = Context({
            'title': 'Sal Version',
            'data': sal_info,
            'theid': theid,
            'page': page
        })
        return t.render(c)

    def filter_machines(self, machines, data):

        machines = machines.filter(sal_version__exact=data)

        title = 'Machines running version ' + data + ' of Sal'
        return machines, title
