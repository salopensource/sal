# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime

class Migration(migrations.Migration):

    dependencies = [
        ('server', '0013_auto_20150816_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.DateTimeField(default=datetime.datetime.now()),
            preserve_default=False,
        ),
    ]
