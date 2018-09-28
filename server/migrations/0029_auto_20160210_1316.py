from __future__ import unicode_literals

from django.db import models, migrations

from server.models import *


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0028_auto_20160207_1406'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstalledUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('update', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('update_version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('display_name', models.CharField(max_length=255, null=True, blank=True)),
                ('installed', models.BooleanField()),
                ('machine', models.ForeignKey(related_name='installed_updates', to='server.Machine')),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='installedupdate',
            unique_together=set([('machine', 'update', 'update_version',)]),
        ),
    ]
