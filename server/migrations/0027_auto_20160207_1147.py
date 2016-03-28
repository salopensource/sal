# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0026_auto_20160207_1142'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['name']},
        ),
        migrations.RemoveField(
            model_name='report',
            name='order',
        ),
    ]
