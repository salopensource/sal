

from django.db import models, migrations
from django.db.models import Q

from server.models import *


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
        ('server', '0030_auto_20160212_1810'),
    ]

    operations = [
        migrations.RunPython(fix_hostname),
    ]
