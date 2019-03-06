"""Cleans up plugin script submissions and update histories that exceed the retention limit"""


import datetime
import gc
from time import sleep

from django.core.management.base import BaseCommand
from django.conf import settings
import django.utils.timezone

import server.utils
from server.models import (PluginScriptSubmission, HistoricalFact, Machine, ManagedItemHistory,
                           ManagementSource)


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

        # Clear out-of-date ManagedItemHistories
        ManagedItemHistory.objects.filter(recorded__lt=datelimit).delete()

        for source in ManagementSource.objects.exclude(name__in=('Machine', 'Sal')):
            if (not source.manageditem_set.count()
                    and not source.manageditemhistory_set.count()  # noqa
                    and not source.facts.count()  # noqa
                    and not source.historical_facts.count()  # noqa
                    and not source.messages.count()):  # noqa
                source.delete()

        HistoricalFact.objects.filter(fact_recorded__lt=datelimit).delete()

        try:
            inactive_undeploy = int(settings.INACTIVE_UNDEPLOYED)

            if inactive_undeploy > 0:
                now = django.utils.timezone.now()
                inactive_days = now - datetime.timedelta(days=inactive_undeploy)
                Machine.deployed_objects.filter(
                    last_checkin__lte=inactive_days).update(deployed=False)
        except Exception:
            pass

        gc.collect()
