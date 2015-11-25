# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0021_auto_20151125_1301'),
    ]

    operations = [
        migrations.AddField(
            model_name='updatehistory',
            name='pending_recorded',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='machine',
            name='install_log',
            field=models.TextField(null=True, blank=True),
        ),
    ]
