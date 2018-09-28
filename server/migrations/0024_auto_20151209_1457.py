

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_squashed_0023_auto_20151130_1036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='install_log_hash',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
    ]
