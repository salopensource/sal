'''
Cleans up old searches and rebuilds search fields cache
'''

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from datetime import datetime, timedelta, date
import django.utils.timezone
from server.models import *
from search.models import *
from inventory.models import *
import server.utils as utils
import datetime
import server.utils
from time import sleep
import operator
from django.db.models import Q


class Command(BaseCommand):
    help = 'Cleans up old searches and rebuilds search fields cache'
    def add_arguments(self, parser):
        parser.add_argument('sleep_time', type=int, nargs='?', default=0)

    def handle(self, *args, **options):
        old_searches = SavedSearch.objects.filter(created__lt=datetime.datetime.today()-datetime.timedelta(days=30), save_search=False)
        old_searches.delete()

        search_fields = []

        skip_fields = [
            'id',
            'report',
            'activity',
            'errors',
            'warnings',
            'install_log',
            'puppet_errors',
            'install_log_hash'
        ]

        inventory_fields = [
            'Name',
            'Bundle ID',
            'Bundle Name',
            'Path'
        ]

        facts = Fact.objects.values('fact_name').distinct()
        conditions = Condition.objects.values('condition_name').distinct()
        plugin_sript_rows = PluginScriptRow.objects.values('pluginscript_name', 'submission__plugin').distinct()
        app_versions = Application.objects.values('name', 'bundleid').distinct()

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

        for inventory_field in inventory_fields:
            cached_item = SearchFieldCache(search_model='Application Inventory', search_field=inventory_field)
            search_fields.append(cached_item)
            if server.utils.is_postgres() == False:
                cached_item.save()

        for app in app_versions:
            string = '%s=>%s' %(app['name'], app['bundleid'])
            cached_item = SearchFieldCache(search_model='Application Version', search_field=string)
            search_fields.append(cached_item)
            if server.utils.is_postgres() == False:
                cached_item.save()

        if server.utils.is_postgres() == True:
            SearchFieldCache.objects.bulk_create(search_fields)

        # make sure this in an int:
        try:
            inactive_undeploy = int(settings.INACTIVE_UNDEPLOYED)

            if inactive_undeploy > 0:
                now = django.utils.timezone.now()
                inactive_days = now - timedelta(days=inactive_undeploy)
                machines_to_inactive = Machine.deployed_objects.all().filter(last_checkin__lte=inactive_days).update(deployed=False)
        except:
            pass

        # Build the fact and condition cache
        items_to_be_inserted = []
        SearchCache.objects.all().delete()
        if settings.SEARCH_FACTS != []:
            queries = []
            for f in settings.SEARCH_FACTS:
                queries.append(Q(fact_name=f))
            qs = Q()
            for query in queries:
                qs = qs | query

            facts = Fact.objects.filter(qs)
            for fact in facts:
                cached_item = SearchCache(machine=fact.machine, search_item=fact.fact_data)
                items_to_be_inserted.append(cached_item)
                if server.utils.is_postgres() == False:
                    cached_item.save()

        if settings.SEARCH_CONDITIONS != []:
            queries = []
            for f in settings.SEARCH_CONDITIONS:
                queries.append(Q(condition_name=f))

            qs = Q()
            for query in queries:
                qs = qs | query
                
            conditions = Condition.objects.filter(qs)
            for condition in conditions:
                cached_item = SearchCache(machine=condition.machine, search_item=condition.condition_data)
                items_to_be_inserted.append(cached_item)
                if server.utils.is_postgres() == False:
                    cached_item.save()       

        if server.utils.is_postgres() == True and items_to_be_inserted != []:
            SearchCache.objects.bulk_create(items_to_be_inserted)
        sleep_time = options['sleep_time']
        sleep(sleep_time)
