from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0034_auto_20160219_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fact',
            name='fact_name',
            field=models.TextField(),
        ),
    ]
