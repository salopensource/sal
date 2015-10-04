# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='License',
            fields=[
                ('item_name', models.CharField(max_length=64, unique=True, serialize=False, primary_key=True)),
                ('total', models.IntegerField(default=0)),
                ('cost_per_seat', models.IntegerField(default=0)),
                ('inventory_name', models.CharField(max_length=256, blank=True)),
                ('inventory_version', models.CharField(max_length=32, blank=True)),
                ('inventory_bundleid', models.CharField(max_length=256, blank=True)),
                ('inventory_bundlename', models.CharField(max_length=256, blank=True)),
                ('inventory_path', models.CharField(max_length=1024, blank=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['item_name'],
            },
        ),
    ]
