from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0024_auto_20151209_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='updatehistoryitem',
            name='uuid',
            field=models.CharField(max_length=100, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='updatehistory',
            name='update_type',
            field=models.CharField(max_length=254, verbose_name=b'Update Type', choices=[
                                   (b'third_party', b'3rd Party'), (b'apple', b'Apple')]),
        ),
        migrations.AlterField(
            model_name='updatehistory',
            name='version',
            field=models.CharField(max_length=254, db_index=True),
        ),
        migrations.AlterField(
            model_name='updatehistoryitem',
            name='status',
            field=models.CharField(max_length=254, verbose_name=b'Status', choices=[(
                b'pending', b'Pending'), (b'error', b'Error'), (b'install', b'Install'), (b'removal', b'Removal')]),
        ),
    ]
