# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0027_auto_20160207_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='plugin',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='report',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
    ]
