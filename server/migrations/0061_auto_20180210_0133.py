# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-02-10 01:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0060_machine_broken_client'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='puppet_version',
            field=models.CharField(blank=True, db_index=True, max_length=256, null=True),
        ),
    ]
