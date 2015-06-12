# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0002_plugin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plugin',
            name='order',
            field=models.IntegerField(),
        ),
    ]
