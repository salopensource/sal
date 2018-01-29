# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0015_auto_20150819_1501'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='business_unit',
            field=models.ForeignKey(default=1, to='server.BusinessUnit', on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
