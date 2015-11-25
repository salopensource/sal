# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0019_auto_20151124_1806'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='install_log',
            field=models.TextField(null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='install_log_hash',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
    ]
