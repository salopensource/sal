from __future__ import unicode_literals

from django.db import models, migrations

from server.models import *


def enable_plugins(apps, schema_editor):

    Machine = apps.get_model("server", "Machine")

    InstalledUpdate = apps.get_model("server", "InstalledUpdate")

    Report = apps.get_model("server", "Report")

    report_count = Report.objects.exclude(name='InstallReport').count()
    if report_count == 0:

        # shard_report = Report(name='ShardReport')
        # shard_report.save()

        install_report = Report(name='MunkiInfo')
        install_report.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0036_auto_20160229_1126'),
    ]

    operations = [
        migrations.RunPython(enable_plugins),
    ]
