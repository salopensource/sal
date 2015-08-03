# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0004_auto_20150623_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='manifest',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='operating_system',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
    ]
