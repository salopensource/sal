# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0018_auto_20151124_1654'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateHistoryItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('recorded', models.DateTimeField()),
                ('status', models.CharField(max_length=255, verbose_name=b'Status', choices=[
                 (b'pending', b'Pending'), (b'error', b'Error'), (b'success', b'Success')])),
            ],
        ),
        migrations.AlterModelOptions(
            name='updatehistory',
            options={'ordering': ['name']},
        ),
        migrations.AlterUniqueTogether(
            name='updatehistory',
            unique_together=set([('machine', 'name', 'version')]),
        ),
        migrations.AddField(
            model_name='updatehistoryitem',
            name='update_history',
            field=models.ForeignKey(to='server.UpdateHistory'),
        ),
        migrations.RemoveField(
            model_name='updatehistory',
            name='recorded',
        ),
        migrations.RemoveField(
            model_name='updatehistory',
            name='status',
        ),
    ]
