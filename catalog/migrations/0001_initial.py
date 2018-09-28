from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0001_squashed_0023_auto_20151130_1036'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('name', models.CharField(max_length=253)),
                ('sha256hash', models.CharField(max_length=64)),
                ('machine_group', models.ForeignKey(to='server.MachineGroup')),
            ],
            options={
                'ordering': ['name', 'machine_group'],
            },
        ),
    ]
