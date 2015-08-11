# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0008_auto_20150811_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apikey',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='public_key',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
