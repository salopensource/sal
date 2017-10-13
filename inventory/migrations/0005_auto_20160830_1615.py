# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_20160907_0905'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='inventoryitem',
            options={'ordering': ['application', '-version']},
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
    ]
