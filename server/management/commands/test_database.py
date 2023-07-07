"""Builds a randomized database for testing

This is a work in progress; please feel free to add as needed. It was
originally written to populate data for testing the application
inventory, but could be expanded to generate an entire fake Sal database
"""

import datetime
import random

try:
    from faker import Faker
except ImportError:
    Faker = None

from django.core.management.base import BaseCommand, CommandError

from inventory.models import Application, InventoryItem, Inventory
from server.models import Machine, BusinessUnit, MachineGroup


class Command(BaseCommand):
    help = (
        "Generates a Sal database for testing. WARNING: This drops ALL existing data!"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apps",
            "-a",
            help="Number of applications to create",
            default=10000,
            type=int,
        )
        parser.add_argument(
            "--items",
            "-i",
            help="Number of inventory_items to create",
            default=10000,
            type=int,
        )
        parser.add_argument(
            "--machines",
            "-m",
            help="Number of machines to create.",
            default=100,
            type=int,
        )

    def handle(self, *args, **options):
        if Faker is None:
            raise CommandError("Please install the Faker package: `pip install faker`")

        # Clean up existing database
        Machine.objects.all().delete()
        BusinessUnit.objects.all().delete()
        MachineGroup.objects.all().delete()
        Application.objects.all().delete()
        InventoryItem.objects.all().delete()
        Inventory.objects.all().delete()

        Faker.seed(0)
        fake = Faker()

        # For now at least, create one BU with one MG in it.
        test_bu = BusinessUnit.objects.create(name="Inventory Test BU")
        test_mg = MachineGroup.objects.create(
            business_unit=test_bu,
            name="Inventory Test MG",
        )

        # Create some machines to have inventory
        for _ in range(options["machines"]):
            machine_dict = {
                "machine_group": test_mg,
                "serial": fake.unique.bothify("??##??##???").upper(),
                "hostname": fake.unique.hostname(0),
                "last_checkin": datetime.datetime.now(tz=datetime.timezone.utc),
            }
            Machine.objects.create(**machine_dict)

        machines = Machine.objects.all()
        for machine in machines:
            Inventory.objects.create(machine=machine, sha256hash=fake.sha256())

        app_count = options["apps"]
        inventory_item_count = options["items"]
        item_per_app = int(inventory_item_count / app_count)

        for _ in range(app_count):
            bundle_id = fake.unique.domain_name(3)
            name = fake.text(max_nb_chars=10)
            app_dict = {
                "bundleid": bundle_id,
                "name": name,
                "bundlename": name,
            }
            app = Application.objects.create(**app_dict)
            for _ in range(item_per_app):
                inventory_item = {
                    "application": app,
                    "version": fake.numerify("%!.%!"),
                    "path": fake.file_path(absolute=True),
                }
                InventoryItem.objects.create(
                    machine=random.choice(machines), **inventory_item
                )

        # TODO: But why?
        print(
            "For some reason, if you run this command multiple times, the results are not "
            "immediately available. It can help to just restart the service.")
