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

class Command(BaseCommand):
    help = 'Cleans up old searches and rebuilds search fields cache'

    def handle(self, *args, **options):
        old_searches = SavedSearch.objects.filter(created__lt=datetime.datetime.today()-datetime.timedelta(days=30), save_search=False)
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
            int(settings.INACTIVE_UNDEPLOYED)

            if settings.INACTIVE_UNDEPLOYED > 0:
                now = django.utils.timezone.now()
                inactive_days = now - timedelta(days=settings.INACTIVE_UNDEPLOYED)
                machines_to_inactive = Machines.deployed_objects.all().
                                        filter(last_checkin__gte=inactive_days).
                                        update(deployed=False)
        except:
            pass
