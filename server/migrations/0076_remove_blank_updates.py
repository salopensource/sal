from __future__ import unicode_literals

from server.models import *
from django.db import migrations, models


def clean_updates(apps, schema_editor):
    """
    Make sure we don't have any pending updates without a version, this makes
    the plugin barf
    """

    PendingAppleUpdate = apps.get_model("server", "PendingAppleUpdate")
    updates_to_clean = PendingAppleUpdate.objects.filter(update_version='')
    for update_to_clean in updates_to_clean:
        update_to_clean.update_version = '0'
        update_to_clean.save()

    PendingUpdate = apps.get_model("server", "PendingUpdate")
    updates_to_clean = PendingUpdate.objects.filter(update_version='')
    for update_to_clean in updates_to_clean:
        update_to_clean.update_version = '0'
        update_to_clean.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0075_machine_activity'),
    ]

    operations = [
        migrations.RunPython(clean_updates),
    ]