# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0013_auto_20150816_1652'),
    ]

    operations = [
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
