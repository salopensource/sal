# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from server.models import *
from django.db import migrations, models

def plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = Plugin(name=plugin_name, order=utils.UniquePluginOrder())
        plugin.save()
    return redirect('plugins_page')


def clean_model_names(apps, schema_editor):
    """
    Non-macos devices will have been given an incorrrect friendly
    name. Let's get those and clean up
    """

    Machine = apps.get_model("server", "Machine")
    machines_to_clean = Machine.objects.exclude(os_family='Darwin')
    for machine_to_clean in machines_to_clean:
        machine_to_clean.machine_model_friendly = ''
        machine_to_clean.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0063_remove_machinedetailplugin_type'),
    ]

    operations = [
        migrations.RunPython(clean_model_names),
    ]
