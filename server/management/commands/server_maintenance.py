"""Cleans up plugin script submissions and update histories that exceed the retention limit"""


import datetime
import gc
from time import sleep

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
import django.utils.timezone

import server.utils
from server.models import PluginScriptSubmission, UpdateHistory, UpdateHistoryItem, HistoricalFact


class Command(BaseCommand):
    help = (
        'Cleans up plugin script submissions and update histories that exceed the retention limit')

    def add_arguments(self, parser):
        parser.add_argument('sleep_time', type=int, nargs='?', default=0)

    def handle(self, *args, **options):

        sleep_time = options['sleep_time']
        sleep(sleep_time)

        historical_days = server.utils.get_setting('historical_retention')
        datelimit = django.utils.timezone.now() - datetime.timedelta(days=historical_days)

        # Clear out too-old plugin script submissions.
        PluginScriptSubmission.objects.filter(recorded__lt=datelimit).delete()

        # Clean up UpdateHistory and items which are over our retention
        # limit and are no longer managed, or which have no history items.

        for history in UpdateHistory.objects.all():
            try:
                latest = history.updatehistoryitem_set.latest('recorded').recorded
            except UpdateHistoryItem.DoesNotExist:
                history.delete()
                continue

            if latest < datelimit:
                history.delete()

        HistoricalFact.objects.filter(fact_recorded__lt=datelimit).delete()

        gc.collect()
