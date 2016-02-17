# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20151026_0845'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('bundleid', models.CharField(max_length=255, db_index=True)),
                ('bundlename', models.CharField(max_length=255, db_index=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AlterModelOptions(
            name='inventoryitem',
            options={},
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='bundleid',
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='bundlename',
        ),
        migrations.RemoveField(
            model_name='inventoryitem',
            name='name',
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='application',
            field=models.ForeignKey(default=0, to='inventory.Application'),
            preserve_default=False,
        ),
    ]
