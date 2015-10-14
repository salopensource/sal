from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils

class TopProcesses(IPlugin):
    def plugin_type(self):
        return 'osquery'

    def get_queries(self):
        output = [{'name':'top_processes','query':'select name from processes;', 'interval':'3600'}]
        return output

    def show_widget(self, page, machines=None, theid=None):
        # The data is data is pulled from the database and passed to a template.
        
        # There are three possible views we're going to be rendering to - front, bu_dashbaord and group_dashboard. If page is set to bu_dashboard, or group_dashboard, you will be passed a business_unit or machine_group id to use (mainly for linking to the right search).
        if page == 'front':
            t = loader.get_template('topprocesses/templates/front.html')
        
        if page == 'bu_dashboard':
            t = loader.get_template('topprocesses/templates/id.html')
        
        if page == 'group_dashboard':
            t = loader.get_template('topprocesses/templates/id.html')
        
        if machines:
            try:
                info = OSQueryColumn.objects.filter(osquery_result__name='pack_sal_top_processes').filter(osquery_result__machine=machines).filter(column_name='name').values('column_data').annotate(data_count=Count('column_data')).order_by('-data_count')[:100:1]
            except:
                info = []
        else:
            info = []
        c = Context({
            'title': 'Top Processes',
            'data': info,
            'theid': theid,
            'page': page
        })
        return t.render(c), 4
    
    def filter_machines(self, machines, data):
        # You will be passed a QuerySet of machines, you then need to perform some filtering based on the 'data' part of the url from the show_widget output. Just return your filtered list of machines and the page title.
        
        machines = machines.filter(osquery_results__osquery_columns__column_data__exact=data).filter(osquery_results__name__exact='pack_sal_top_processes').distinct()
        
        return machines, 'Machines running '+data
        