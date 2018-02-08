# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import get_object_or_404
from django.db import models, migrations


def add_initial_date(apps, schema_editor):
    Machine = apps.get_model("server", "Machine")
    for machine in Machine.objects.all():
        if not machine.first_checkin:
            machine.first_checkin = machine.last_checkin
            machine.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0005_auto_20150717_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='first_checkin',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='sal_version',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.RunPython(add_initial_date),
    ]
