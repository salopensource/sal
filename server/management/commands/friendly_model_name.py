"""Retrieves the friendly model name for machines that don't have one yet."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

import server.utils as utils
from server.models import Machine


class Command(BaseCommand):
    help = 'Retrieves friendly model names for machines without one'

    def handle(self, *args, **options):
        # Get all the machines without a friendly model name and have a model
        no_friendly = Machine.objects.filter(
            Q(machine_model_friendly__isnull=True) |
            Q(machine_model_friendly='')
        ).exclude(machine_model__isnull=True).exclude(machine_model='').filter(os_family='Darwin')
        for machine in no_friendly[:100]:
            print(f'Processing {machine}')
            machine.machine_model_friendly = utils.friendly_machine_model(machine)
            machine.save()
