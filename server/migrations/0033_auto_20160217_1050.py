# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from server.models import *
from django.db import models, migrations
from django.db.models import Q
import plistlib


def fix_hostname(apps, schema_editor):

    Machine = apps.get_model("server", "Machine")

    machines = Machine.objects.filter(hostname__isnull=True)
    for machine in machines:
        machine.hostname = machine.serial
        machine.save()

    machines = Machine.objects.filter(hostname__exact='')
    for machine in machines:
        machine.hostname = machine.serial
        machine.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0032_auto_20160218_0939'),
    ]

    operations = [
        migrations.RunPython(fix_hostname),
    ]
