# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0020_auto_20151125_0848'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='updatehistoryitem',
            options={'ordering': ['recorded']},
        ),
        migrations.AddField(
            model_name='updatehistoryitem',
            name='extra',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='updatehistoryitem',
            name='status',
            field=models.CharField(max_length=255, verbose_name=b'Status', choices=[(
                b'pending', b'Pending'), (b'error', b'Error'), (b'install', b'Install'), (b'removal', b'Removal')]),
        ),
        migrations.AlterUniqueTogether(
            name='updatehistory',
            unique_together=set([('machine', 'name', 'version', 'update_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='updatehistoryitem',
            unique_together=set([('update_history', 'recorded', 'status')]),
        ),
    ]
