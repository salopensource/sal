

from django.db import models, migrations
from django.conf import settings


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# server.migrations.0006_auto_20150811_0811

def add_initial_date(apps, schema_editor):
    Machine = apps.get_model("server", "Machine")
    for machine in Machine.objects.all():
        if not machine.first_checkin:
            machine.first_checkin = machine.last_checkin
            machine.save()


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
            field=models.ForeignKey(related_name='historical_facts', to='server.Machine'),
        ),
        migrations.AddField(
            model_name='fact',
            name='machine',
            field=models.ForeignKey(related_name='facts', to='server.Machine'),
        ),
        migrations.AddField(
            model_name='condition',
            name='machine',
            field=models.ForeignKey(related_name='conditions', to='server.Machine'),
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
        migrations.CreateModel(
            name='Plugin',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=512)),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.RemoveField(
            model_name='apikey',
            name='read_only',
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='machine',
            field=models.ForeignKey(related_name='pending_apple_updates', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='machine',
            field=models.ForeignKey(related_name='pending_updates', to='server.Machine'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='manifest',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='operating_system',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='first_checkin',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='sal_version',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.RunPython(
            code=add_initial_date,
        ),
        migrations.AlterField(
            model_name='plugin',
            name='name',
            field=models.CharField(unique=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='plugin',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='public_key',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.CreateModel(
            name='OSQueryColumn',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('column_name', models.TextField()),
                ('column_data', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='OSQueryResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('hostidentifier', models.CharField(max_length=255, null=True, blank=True)),
                ('unix_time', models.IntegerField(null=True, blank=True)),
                ('action', models.CharField(max_length=255, null=True, blank=True)),
                ('machine', models.ForeignKey(related_name='osquery_results', to='server.Machine')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='plugin',
            name='type',
            field=models.CharField(default=b'facter', max_length=255, choices=[(b'facter', b'Facter'), (
                b'munkicondition', b'Munki Condition'), (b'osquery', b'osquery'), (b'builtin', b'Built In')]),
        ),
        migrations.AddField(
            model_name='osquerycolumn',
            name='osquery_result',
            field=models.ForeignKey(related_name='osquery_columns', to='server.OSQueryResult'),
        ),
        migrations.AlterUniqueTogether(
            name='osqueryresult',
            unique_together=set([('unix_time', 'name')]),
        ),
        migrations.RemoveField(
            model_name='osqueryresult',
            name='action',
        ),
        migrations.AddField(
            model_name='osquerycolumn',
            name='action',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.CreateModel(
            name='SalSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('value', models.TextField()),
            ],
        ),
        migrations.AlterModelOptions(
            name='osqueryresult',
            options={'ordering': ['unix_time']},
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='name',
            field=models.CharField(default=' ', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='display_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update_version',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='osqueryresult',
            unique_together=set([]),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='public_key',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='first_checkin',
            field=models.DateTimeField(db_index=True, auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='hd_space',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='hd_total',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='last_checkin',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='last_puppet_run',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='manifest',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='memory',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='memory_kb',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='munki_version',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='operating_system',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='puppet_errors',
            field=models.IntegerField(default=0, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='serial',
            field=models.CharField(unique=True, max_length=100, db_index=True),
        ),
        migrations.AlterField(
            model_name='machinegroup',
            name='key',
            field=models.CharField(null=True, editable=False, max_length=255,
                                   blank=True, unique=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='hostidentifier',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='osqueryresult',
            name='unix_time',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingappleupdate',
            name='update_version',
            field=models.CharField(db_index=True, max_length=256, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='pendingupdate',
            name='update_version',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='condition',
            name='condition_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='condition',
            name='condition_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='fact',
            name='fact_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='fact',
            name='fact_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalfact',
            name='fact_data',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='historicalfact',
            name='fact_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='machine',
            name='sal_version',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='osquerycolumn',
            name='column_name',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.CreateModel(
            name='UpdateHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('update_type', models.CharField(max_length=255, verbose_name=b'Update Type',
                                                 choices=[(b'third_party', b'3rd Party'), (b'apple', b'Apple')])),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('version', models.CharField(max_length=255, db_index=True)),
                ('recorded', models.DateTimeField()),
                ('status', models.CharField(max_length=255, verbose_name=b'Status', choices=[
                 (b'pending', b'Pending'), (b'error', b'Error'), (b'success', b'Success')])),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['recorded'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='updatehistory',
            unique_together=set([('machine', 'name', 'version', 'update_type', 'status')]),
        ),
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
        migrations.AddField(
            model_name='machine',
            name='install_log',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='machine',
            name='install_log_hash',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AlterModelOptions(
            name='updatehistoryitem',
            options={'ordering': ['recorded']},
        ),
        migrations.AddField(
            model_name='updatehistoryitem',
            name='extra',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='updatehistoryitem',
            name='status',
            field=models.CharField(max_length=255, verbose_name=b'Status', choices=[(
                b'pending', b'Pending'), (b'error', b'Error'), (b'install', b'Install'), (b'removal', b'Removal')]),
        ),
        migrations.AlterUniqueTogether(
            name='updatehistory',
            unique_together=set([('machine', 'name', 'version', 'update_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='updatehistoryitem',
            unique_together=set([('update_history', 'recorded', 'status')]),
        ),
        migrations.AddField(
            model_name='updatehistory',
            name='pending_recorded',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterModelOptions(
            name='updatehistoryitem',
            options={'ordering': ['-recorded']},
        ),
    ]
