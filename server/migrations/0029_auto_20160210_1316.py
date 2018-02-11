# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from server.models import *
from django.db import models, migrations
import plistlib

# def populate_installed_items(apps, schema_editor):
#
#     Machine = apps.get_model("server", "Machine")
#
#     InstalledUpdate = apps.get_model("server", "InstalledUpdate")
#
#     Report = apps.get_model("server", "Report")
#
#     shard_report = Report(name='ShardReport')
#     shard_report.save()
#
#     install_report = Report(name='InstallReport')
#     install_report.save()
#
#     for machine in Machine.objects.all():
#         report = machine.report
#         updates = machine.installed_updates.all()
#         updates.delete()
#
#         try:
#             report_data = plistlib.readPlistFromString(report)
#         except Exception:
#             try:
#                 report_data = plistlib.readPlistFromString(
#                                         report.encode('UTF-8'))
#             except Exception:
#                 report_data = {}
#
#         if 'ManagedInstalls' in report_data:
#             for update in report_data.get('ManagedInstalls'):
#                 display_name = update.get('display_name', update['name'])
#                 update_name = update.get('name')
#                 version = str(update.get('installed_version', 'UNKNOWN'))
#                 installed = update.get('installed', False)
#
#                 if version != 'UNKNOWN':
#                     installed_update = InstalledUpdate(machine=machine,
#                     display_name=display_name, update_version=version,
#                     update=update_name, installed=installed)
#                     installed_update.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0028_auto_20160207_1406'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstalledUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('update', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('update_version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('display_name', models.CharField(max_length=255, null=True, blank=True)),
                ('installed', models.BooleanField()),
                ('machine', models.ForeignKey(related_name='installed_updates', to='server.Machine', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='installedupdate',
            unique_together=set([('machine', 'update', 'update_version',)]),
        ),
        # migrations.RunPython(populate_installed_items),
    ]
