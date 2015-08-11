# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0007_auto_20150811_0813'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plugin',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]