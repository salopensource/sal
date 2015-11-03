# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0016_auto_20151026_0851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='condition',
            name='condition_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='condition',
            name='condition_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='fact',
            name='fact_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='fact',
            name='fact_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalfact',
            name='fact_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='historicalfact',
            name='fact_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='sal_version',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
