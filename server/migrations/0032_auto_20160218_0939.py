from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0031_auto_20160217_0918'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='pendingappleupdate',
            unique_together=set([('machine', 'update', 'update_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='pendingupdate',
            unique_together=set([('machine', 'update', 'update_version')]),
        ),
    ]
