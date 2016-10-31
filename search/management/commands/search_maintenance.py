'''
Cleans up old searches and rebuilds search fields cache
'''

from django.core.management.base import BaseCommand, CommandError
from server.models import *
from search.models import *
from django.db.models import Q
import server.utils as utils
import datetime
import server.utils

class Command(BaseCommand):
    help = 'Cleans up old searches and rebuilds search fields cache'

    def handle(self, *args, **options):
        old_searches = SavedSearch.objects.filter(created__lt=datetime.datetime.today()-datetime.timedelta(days=30))
        old_searches.delete()

        search_fields = []

        skip_fields = [
            'id',
            'machine_group',
            'report',
            'activity',
            'errors',
            'warnings',
            'install_log',
            'puppet_errors',
            'install_log_hash'
        ]
        facts = Fact.objects.values('fact_name').distinct()
        conditions = Condition.objects.values('condition_name').distinct()
        plugin_sript_rows = PluginScriptRow.objects.values('pluginscript_name', 'submission__plugin').distinct()

        # force evaluation so we can safely delete the existing data
        if facts:
            pass
        if conditions:
            pass
        if plugin_sript_rows:
            pass

        old_cache = SearchFieldCache.objects.all()
        old_cache.delete()
        for f in Machine._meta.fields:
            if f.name not in skip_fields:
                cached_item = SearchFieldCache(search_model='Machine', search_field=f.name)
                search_fields.append(cached_item)
                if server.utils.is_postgres() == False:
                    cached_item.save()

        for fact in facts:
            cached_item = SearchFieldCache(search_model='Facter', search_field=fact['fact_name'])
            search_fields.append(cached_item)
            if server.utils.is_postgres() == False:
                cached_item.save()

        for condition in conditions:
            cached_item = SearchFieldCache(search_model='Condition', search_field=condition['condition_name'])
            search_fields.append(cached_item)
            if server.utils.is_postgres() == False:
                cached_item.save()

        for row in plugin_sript_rows:
            string = '%s=>%s' %(row['submission__plugin'], row['pluginscript_name'])
            cached_item = SearchFieldCache(search_model='External Script', search_field=string)
            search_fields.append(cached_item)
            if server.utils.is_postgres() == False:
                cached_item.save()

        if server.utils.is_postgres() == True:
            SearchFieldCache.objects.bulk_create(search_fields)
