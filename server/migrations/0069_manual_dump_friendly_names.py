

from server.models import *
from django.db import migrations, models


def clean_model_names(apps, schema_editor):
    """
    Non-macos devices will have been given an incorrrect friendly
    name. Let's get those and clean up
    """

    Machine = apps.get_model("server", "Machine")
    machines_to_clean = Machine.objects.all()
    for machine_to_clean in machines_to_clean:
        machine_to_clean.machine_model_friendly = ''
        machine_to_clean.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0068_auto_20180313_1440'),
    ]

    operations = [
        migrations.RunPython(clean_model_names),
    ]