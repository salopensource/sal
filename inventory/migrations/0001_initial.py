# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_squashed_0023_auto_20151130_1036'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('datestamp', models.DateTimeField(auto_now=True)),
                ('sha256hash', models.CharField(max_length=64)),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['datestamp'],
            },
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('version', models.CharField(max_length=32)),
                ('bundleid', models.CharField(max_length=255)),
                ('bundlename', models.CharField(max_length=255)),
                ('path', models.TextField()),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['name', '-version'],
            },
        ),
    ]
