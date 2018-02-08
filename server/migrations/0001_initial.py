# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('public_key', models.CharField(max_length=256)),
                ('private_key', models.CharField(max_length=256)),
                ('name', models.CharField(max_length=256)),
                ('has_been_seen', models.BooleanField(default=False)),
                ('read_only', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='BusinessUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('condition_name', models.TextField()),
                ('condition_data', models.TextField()),
            ],
            options={
                'ordering': ['condition_name'],
            },
        ),
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('fact_name', models.TextField()),
                ('fact_data', models.TextField()),
            ],
            options={
                'ordering': ['fact_name'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalFact',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('fact_name', models.TextField()),
                ('fact_data', models.TextField()),
                ('fact_recorded', models.DateTimeField(db_index=True)),
            ],
            options={
                'ordering': ['fact_name', 'fact_recorded'],
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('serial', models.CharField(unique=True, max_length=100)),
                ('hostname', models.CharField(max_length=256, null=True, blank=True)),
                ('operating_system', models.CharField(max_length=256)),
                ('memory', models.CharField(max_length=256, null=True, blank=True)),
                ('memory_kb', models.IntegerField(default=0)),
                ('munki_version', models.CharField(max_length=256, null=True, blank=True)),
                ('manifest', models.CharField(max_length=256)),
                ('hd_space', models.CharField(max_length=256, null=True, blank=True)),
                ('hd_total', models.CharField(max_length=256, null=True, blank=True)),
                ('hd_percent', models.CharField(max_length=256, null=True, blank=True)),
                ('console_user', models.CharField(max_length=256, null=True, blank=True)),
                ('machine_model', models.CharField(max_length=256, null=True, blank=True)),
                ('cpu_type', models.CharField(max_length=256, null=True, blank=True)),
                ('cpu_speed', models.CharField(max_length=256, null=True, blank=True)),
                ('os_family', models.CharField(default=b'Darwin', max_length=256, verbose_name=b'OS Family', choices=[
                 (b'Darwin', b'OS X'), (b'Windows', b'Windows'), (b'Linux', b'Linux')])),
                ('last_checkin', models.DateTimeField(null=True, blank=True)),
                ('report', models.TextField(null=True)),
                ('errors', models.IntegerField(default=0)),
                ('warnings', models.IntegerField(default=0)),
                ('activity', models.TextField(null=True, editable=False, blank=True)),
                ('puppet_version', models.TextField(null=True, blank=True)),
                ('last_puppet_run', models.DateTimeField(null=True, blank=True)),
                ('puppet_errors', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['hostname'],
            },
        ),
        migrations.CreateModel(
            name='MachineGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('key', models.CharField(max_length=255, unique=True, null=True, editable=False, blank=True)),
                ('business_unit', models.ForeignKey(to='server.BusinessUnit')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PendingAppleUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('update', models.CharField(max_length=256, null=True, blank=True)),
                ('update_version', models.CharField(max_length=256, null=True, blank=True)),
                ('display_name', models.CharField(max_length=256, null=True, blank=True)),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='PendingUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('update', models.CharField(max_length=256, null=True, blank=True)),
                ('update_version', models.CharField(max_length=256, null=True, blank=True)),
                ('display_name', models.CharField(max_length=256, null=True, blank=True)),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('level', models.CharField(default=b'SO', max_length=2, choices=[
                 (b'SO', b'Stats Only'), (b'RO', b'Read Only'), (b'RW', b'Read Write'), (b'GA', b'Global Admin')])),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='machine',
            name='machine_group',
            field=models.ForeignKey(to='server.MachineGroup'),
        ),
        migrations.AddField(
            model_name='historicalfact',
            name='machine',
            field=models.ForeignKey(to='server.Machine'),
        ),
        migrations.AddField(
            model_name='fact',
            name='machine',
            field=models.ForeignKey(to='server.Machine'),
        ),
        migrations.AddField(
            model_name='condition',
            name='machine',
            field=models.ForeignKey(to='server.Machine'),
        ),
        migrations.AlterUniqueTogether(
            name='apikey',
            unique_together=set([('public_key', 'private_key')]),
        ),
        migrations.AlterUniqueTogether(
            name='pendingupdate',
            unique_together=set([('machine', 'update')]),
        ),
        migrations.AlterUniqueTogether(
            name='pendingappleupdate',
            unique_together=set([('machine', 'update')]),
        ),
    ]
