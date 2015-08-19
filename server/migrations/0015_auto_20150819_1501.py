# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0014_auto_20150817_1646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salsetting',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
