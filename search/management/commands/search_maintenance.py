'''Cleans up old searches and rebuilds search fields cache'''

from time import sleep
import gc

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from inventory.models import *
from server.models import *
from search.models import *
from profiles.models import *
import server.utils

# This is down here because an import * from above is clobbering
import datetime


class Command(BaseCommand):
    help = 'Cleans up old searches and rebuilds search fields cache'

    def add_arguments(self, parser):
        parser.add_argument('sleep_time', type=int, nargs='?', default=0)

    def handle(self, *args, **options):

        sleep_time = options['sleep_time']
        sleep(sleep_time)
        old_searches = SavedSearch.objects.filter(
            created__lt=datetime.datetime.today() - datetime.timedelta(days=30), save_search=False)
        old_searches.delete()

        search_fields = []

        skip_fields = [
            'id',
        ]

        inventory_fields = [
            'Name',
            'Bundle ID',
            'Bundle Name',
            'Path'
        ]

        facts = Fact.objects.values('fact_name').distinct()
        plugin_sript_rows = PluginScriptRow.objects.values(
            'pluginscript_name', 'submission__plugin').distinct()
        app_versions = Application.objects.values('name', 'bundleid').distinct()

        old_cache = SearchFieldCache.objects.all()
        if server.utils.is_postgres() is False:
            old_cache.delete()
        for f in Machine._meta.fields:
            if f.name not in skip_fields:
                cached_item = SearchFieldCache(search_model='Machine', search_field=f.name)
                search_fields.append(cached_item)
                if server.utils.is_postgres() is False:
                    cached_item.save()

        for fact in facts.iterator():
            cached_item = SearchFieldCache(search_model='Facter', search_field=fact['fact_name'])
            search_fields.append(cached_item)
            if server.utils.is_postgres() is False:
                cached_item.save()

        for row in plugin_sript_rows.iterator():
            string = '%s=>%s' % (row['submission__plugin'], row['pluginscript_name'])
            cached_item = SearchFieldCache(search_model='External Script', search_field=string)
            search_fields.append(cached_item)
            if server.utils.is_postgres() is False:
                cached_item.save()

        for inventory_field in inventory_fields:
            cached_item = SearchFieldCache(
                search_model='Application Inventory', search_field=inventory_field)
            search_fields.append(cached_item)
            if server.utils.is_postgres() is False:
                cached_item.save()

        for app in app_versions.iterator():
            string = '%s=>%s' % (app['name'], app['bundleid'])
            cached_item = SearchFieldCache(search_model='Application Version', search_field=string)
            search_fields.append(cached_item)
            if server.utils.is_postgres() is False:
                cached_item.save()

        for f in Profile._meta.fields:
            if f.name not in skip_fields:
                cached_item = SearchFieldCache(search_model='Profile', search_field=f.name)
                search_fields.append(cached_item)
                if server.utils.is_postgres() is False:
                    cached_item.save()

        for f in Payload._meta.fields:
            if f.name not in skip_fields:
                cached_item = SearchFieldCache(search_model='Profile Payload', search_field=f.name)
                search_fields.append(cached_item)
                if server.utils.is_postgres() is False:
                    cached_item.save()

        if server.utils.is_postgres() is True:
            old_cache.delete()
            SearchFieldCache.objects.bulk_create(search_fields)

        # Build the fact cache
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
            for fact in facts.iterator():
                cached_item = SearchCache(machine=fact.machine, search_item=fact.fact_data)
                items_to_be_inserted.append(cached_item)
                if not server.utils.is_postgres():
                    cached_item.save()

        if server.utils.is_postgres() and items_to_be_inserted != []:
            SearchCache.objects.bulk_create(items_to_be_inserted)

        gc.collect()
