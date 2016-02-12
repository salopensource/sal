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
        if isinstance(s, unicode):
            return s.encode('utf-8', errors='replace')
        else:
            return s


    def replace_dots(self,item):
        item['dotVersion'] = item['version'].replace('.','DOT')
        return item

    def widget_content(self, page, machines=None, theid=None):

        if page == 'front':
            t = loader.get_template('shardreport/templates/front.html')
            catalog_objects = Catalog.objects.all()

        if page == 'bu_dashboard':
            t = loader.get_template('shardreport/templates/front.html')
            business_unit = get_object_or_404(BusinessUnit, pk=theid)
            machine_groups = business_unit.machinegroup_set.all()
            catalog_objects = Catalog.objects.filter(machine_group=machine_groups)

        if page == 'group_dashboard':
            t = loader.get_template('shardreport/templates/front.html')
            machine_group = get_object_or_404(MachineGroup, pk=theid)
            catalog_objects = Catalog.objects.filter(machine_group=machine_group)

        shard1 = []
        shard2 = []
        shard3 = []

        for catalog in catalog_objects:
            plist = plistlib.readPlistFromString(self.safe_unicode(catalog.content))
            for item in plist:
                found = False
                if 'installable_condition' in item:
                    if item['installable_condition'] == 'shard <= 25':
                        for shard1_item in shard1:
                            if shard1_item['name'] == item['name'] and shard1_item['version'] == item['version']:
                                found = True
                        if not found:
                            item = self.replace_dots(item)
                            shard1.append(item)
                    elif item['installable_condition'] == 'shard <= 50':
                        for shard2_item in shard2:
                            if shard2_item['name'] == item['name'] and shard2_item['version'] == item['version']:
                                found = True
                        if not found:
                            item = self.replace_dots(item)
                            shard2.append(item)
                    elif item['installable_condition'] == 'shard <= 75':
                        for shard3_item in shard3:
                            if shard3_item['name'] == item['name'] and shard3_item['version'] == item['version']:
                                found = True
                        if not found:
                            item = self.replace_dots(item)
                            shard3.append(item)

        c = Context({
            'title': 'Shard',
            'shard1': shard1,
            'shard2': shard2,
            'shard3': shard3,
            'all_items': shard1+shard2+shard3,
            'plugin': 'ShardReport',
            'page': page,
            'theid': theid
        })
        return t.render(c)
