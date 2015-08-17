# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0014_auto_20150817_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.IntegerField(),
        ),
    ]
