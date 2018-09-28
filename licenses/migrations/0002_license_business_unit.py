from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_squashed_0023_auto_20151130_1036'),
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='business_unit',
            field=models.ForeignKey(default=1, to='server.BusinessUnit'),
            preserve_default=False,
        ),
    ]
