# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from server.models import *
from django.db import migrations, models
from server import utils


def plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = Plugin(name=plugin_name, order=utils.unique_plugin_order())
        plugin.save()
    return redirect('plugins_page')


def enable_plugins(apps, schema_editor):

    Machine = apps.get_model("server", "Machine")

    Plugin = apps.get_model("server", "Plugin")
    new_plugins = ['Encryption', 'Gatekeeper', 'Sip', 'XprotectVersion']
    if Plugin.objects.count() != 0:
        for plugin_name in new_plugins:
            try:
                plugin = Plugin.objects.get(name=plugin_name)
            except Plugin.DoesNotExist:
                plugin = Plugin(name=plugin_name, order=utils.unique_plugin_order())
                plugin.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0046_auto_20160905_1049'),
    ]

    operations = [
        migrations.RunPython(enable_plugins),
    ]
