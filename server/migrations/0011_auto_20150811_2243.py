# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0010_auto_20150811_2209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='osqueryresult',
            name='action',
        ),
        migrations.AddField(
            model_name='osquerycolumn',
            name='action',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
