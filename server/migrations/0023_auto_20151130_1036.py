# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0022_auto_20151125_1811'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='updatehistoryitem',
            options={'ordering': ['-recorded']},
        ),
    ]
