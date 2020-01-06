# Generated by Django 1.10 on 2017-08-22 21:30


import os

from django.conf import settings
from django.db import migrations, models

import sal.plugin
from server.models import Plugin
from utils import text_utils


def update_os_families(apps, schema_editor):
    enabled_plugins = Plugin.objects.all()
    enabled_plugins = apps.get_model("server", "MachineDetailPlugin")
    for item in enabled_plugins.objects.all():
        default_families = ['Darwin', 'Windows', 'Linux', 'ChromeOS']
        plugin = sal.plugin.PluginManager.get_plugin_by_name(item.name)
        if plugin:
            try:
                supported_os_families = plugin.get_supported_os_families()
            except Exception:
                supported_os_families = default_families

            item.os_families = sorted(text_utils.stringify(supported_os_families))
            item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0057_auto_20170822_1421'),
    ]

    operations = [
        migrations.RunPython(update_os_families),
    ]
