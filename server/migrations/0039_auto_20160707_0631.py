# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from server.models import *
from django.db import migrations, models


def enable_plugins(apps, schema_editor):

    Machine = apps.get_model("server", "Machine")

    MachineDetailPlugin = apps.get_model("server", "MachineDetailPlugin")

    plugin_count = MachineDetailPlugin.objects.all().exclude(name='MachineDetailSecurity').count()
    if plugin_count == 0:

        plugin = MachineDetailPlugin(name='MachineDetailSecurity', order=1)
        plugin.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0038_auto_20160704_1005'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineDetailPlugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('order', models.IntegerField()),
                ('type', models.CharField(default=b'builtin', max_length=255, choices=[(b'facter', b'Facter'), (
                    b'munkicondition', b'Munki Condition'), (b'builtin', b'Built In'), (b'custom', b'Custom Script')])),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AlterField(
            model_name='plugin',
            name='type',
            field=models.CharField(default=b'builtin', max_length=255, choices=[(b'facter', b'Facter'), (
                b'munkicondition', b'Munki Condition'), (b'builtin', b'Built In'), (b'custom', b'Custom Script')]),
        ),
        migrations.RunPython(enable_plugins),
    ]
