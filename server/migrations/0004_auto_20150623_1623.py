# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0003_auto_20150612_1123'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='apikey',
            name='read_only',
        ),
        migrations.AlterField(
            model_name='condition',
            name='machine',
            field=models.ForeignKey(related_name='conditions', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='fact',
            name='machine',
            field=models.ForeignKey(related_name='facts', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='historicalfact',
            name='machine',
            field=models.ForeignKey(related_name='historical_facts', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='machine',
            field=models.ForeignKey(related_name='pending_apple_updates', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='machine',
            field=models.ForeignKey(related_name='pending_updates', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='plugin',
            name='name',
            field=models.CharField(unique=True, max_length=512),
        ),
    ]
