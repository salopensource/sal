# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from inventory.models import Application


def migrate_inventoryitems_to_applications(apps, schema_editor):
    inventory_items = apps.get_model("inventory", "InventoryItem")
    apps = apps.get_model("inventory", "Application")
    for item in inventory_items.objects.all():
        app = apps.objects.get(bundleid=item.bundleid, name=item.name,
                               bundlename=item.bundlename)
        item.application = app
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20160216_1756'),
    ]

    operations = [
        migrations.RunPython(migrate_inventoryitems_to_applications),
    ]
