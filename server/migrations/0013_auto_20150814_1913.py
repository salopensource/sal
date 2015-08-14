# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0012_auto_20150811_2243'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('value', models.TextField()),
            ],
        ),
        migrations.AlterModelOptions(
            name='osqueryresult',
            options={'ordering': ['unix_time']},
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='name',
            field=models.CharField(default=' ', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='display_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update_version',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='plugin',
            name='type',
            field=models.CharField(default=b'facter', max_length=255, choices=[(b'facter', b'Facter'), (b'munkicondition', b'Munki Condition'), (b'osquery', b'osquery'), (b'builtin', b'Built In')]),
        ),
    ]
