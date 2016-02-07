from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManager
from django.template import loader, Context
from django.db.models import Count
from server.models import *
from catalog.models import *
from django.shortcuts import get_object_or_404
import server.utils as utils
import plistlib

class ShardReport(IPlugin):
    def plugin_type(self):
        return 'report'

    def widget_width(self):
        return 12

    def get_description(self):
        return 'Information on items in each shard.'

    def get_title(self):
        return 'Shard'

    def safe_unicode(self, s):

        return s.encode('utf-8', errors='replace')

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('shardreport/templates/front.html')

        if page == 'bu_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')

        if page == 'group_dashboard':
            t = loader.get_template('plugins/traffic_lights_id.html')

        shard1 = []
        shard2 = []
        shard3 = []

        for catalog in Catalog.objects.all():
            plist = plistlib.readPlistFromString(self.safe_unicode(catalog.content))
            for item in plist:
                found = False
                if 'installable_condition' in item:
                    if item['installable_condition'] == 'shard <= 25':
                        for shard1_item in shard1:
                            if shard1_item['name'] == item['name'] and shard1_item['version'] == item['version']:
                                found = True
                        if not found:
                            shard1.append(item)
                    elif item['installable_condition'] == 'shard <= 50':
                        shard2.append(item)
                    elif item['installable_condition'] == 'shard <= 75':
                        shard3.append(item)

        c = Context({
            'title': 'Shard',
            'shard1': shard1,
            'shard2': shard2,
            'shard3': shard3,
            'plugin': 'ShardReport',
            'page': page,
            'theid': theid
        })
        return t.render(c)
