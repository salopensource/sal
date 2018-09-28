from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryitem',
            name='bundleid',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='bundlename',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='inventoryitem',
            name='version',
            field=models.CharField(max_length=32, db_index=True),
        ),
    ]
