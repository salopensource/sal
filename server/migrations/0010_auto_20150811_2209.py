# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0009_auto_20150811_1734'),
    ]

    operations = [
        migrations.CreateModel(
            name='OSQueryColumn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('column_name', models.TextField()),
                ('column_data', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='OSQueryResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('hostidentifier', models.CharField(max_length=255, null=True, blank=True)),
                ('unix_time', models.DateTimeField(null=True, blank=True)),
                ('action', models.CharField(max_length=255, null=True, blank=True)),
                ('machine', models.ForeignKey(related_name='osquery_results', to='server.Machine')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='plugin',
            name='type',
            field=models.CharField(default=b'facter', max_length=255, choices=[(b'facter', b'Facter'), (b'munkicondition', b'Munki Condition'), (b'osquery', b'osquery')]),
        ),
        migrations.AddField(
            model_name='osquerycolumn',
            name='osquery_result',
            field=models.ForeignKey(related_name='osquery_columns', to='server.OSQueryResult'),
        ),
        migrations.AlterUniqueTogether(
            name='osqueryresult',
            unique_together=set([('unix_time', 'name')]),
        ),
    ]
