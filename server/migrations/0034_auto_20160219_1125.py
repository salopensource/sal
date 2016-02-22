# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0033_auto_20160217_1050'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='pendingappleupdate',
            unique_together=set([]),
        ),
        migrations.AlterUniqueTogether(
            name='pendingupdate',
            unique_together=set([]),
        ),
    ]
