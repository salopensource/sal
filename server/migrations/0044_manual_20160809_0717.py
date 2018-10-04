
from server.models import *
from django.db import migrations, models


def index_facts(apps, schema_editor):

    Fact = apps.get_model("server", "Fact")

    # MachineDetailPlugin = apps.get_model("server", "MachineDetailPlugin")

    facts = Fact.objects.all()
    for fact in facts:
        fact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0043_auto_20160809_2122'),
    ]

    operations = [
        migrations.RunPython(index_facts),
    ]
