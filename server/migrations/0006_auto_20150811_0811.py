# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0005_auto_20150717_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='first_checkin',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='sal_version',
            field=models.TextField(null=True, blank=True),
        ),
    ]
