# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0015_auto_20150819_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='public_key',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='first_checkin',
            field=models.DateTimeField(db_index=True, auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='hd_space',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='hd_total',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='last_checkin',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='last_puppet_run',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='manifest',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='memory',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='memory_kb',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='munki_version',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='operating_system',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='puppet_errors',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='serial',
            field=models.CharField(unique=True, max_length=100, db_index=True),
        ),
        migrations.AlterField(
            model_name='machinegroup',
            name='key',
            field=models.CharField(null=True, editable=False, max_length=255, blank=True, unique=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='hostidentifier',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update_version',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update_version',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
    ]
