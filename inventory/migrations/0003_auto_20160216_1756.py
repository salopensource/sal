# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from inventory.models import Application


def migrate_inventoryitems_to_applications(apps, schema_editor):
    inventory_items = apps.get_model("inventory", "InventoryItem")
    for item in inventory_items.objects.all():
        try:
            app, _ = Application.objects.get_or_create(
                bundleid=item.bundleid or "",
                name=item.name or "",
                bundlename=item.bundlename or "")
            item.application = app
            item.save()
        except:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20151026_0845'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('bundleid', models.CharField(max_length=255, db_index=True)),
                ('bundlename', models.CharField(max_length=255, db_index=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AlterModelOptions(
            name='inventoryitem',
            options={},
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='bundleid',
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='bundlename',
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='name',
        ),
        migrations.RunPython(migrate_inventoryitems_to_applications),
        migrations.AddField(
            model_name='inventoryitem',
            name='application',
            field=models.ForeignKey(to='inventory.Application'),
            preserve_default=False,
        ),
    ]
