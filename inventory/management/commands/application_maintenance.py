"""Clean up orphaned Application objects."""


import gc
from time import sleep

from django.core.management.base import BaseCommand, CommandError

import server.utils
from inventory.models import Application


class Command(BaseCommand):
    help = 'Cleans up orphaned Application objects.'

    def add_arguments(self, parser):
        parser.add_argument('sleep_time', type=int, nargs='?', default=0)

    def handle(self, *args, **options):

        sleep_time = options['sleep_time']
        sleep(sleep_time)

        # # Clean up orphaned Application objects.
        Application.objects.filter(inventoryitem=None).delete()

        gc.collect()
