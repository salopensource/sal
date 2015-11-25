# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0017_auto_20151103_1800'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_type', models.CharField(max_length=255, verbose_name=b'Update Type', choices=[(b'third_party', b'3rd Party'), (b'apple', b'Apple')])),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(max_length=255, db_index=True)),
                ('recorded', models.DateTimeField()),
                ('status', models.CharField(max_length=255, verbose_name=b'Status', choices=[(b'pending', b'Pending'), (b'error', b'Error'), (b'success', b'Success')])),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['recorded'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='updatehistory',
            unique_together=set([('machine', 'name', 'version', 'update_type', 'status')]),
        ),
    ]
