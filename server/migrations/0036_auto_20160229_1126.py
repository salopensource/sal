

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0035_auto_20160219_1820'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluginScriptRow',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('pluginscript_name', models.TextField()),
                ('pluginscript_data', models.TextField()),
            ],
            options={
                'ordering': ['pluginscript_name'],
            },
        ),
        migrations.CreateModel(
            name='PluginScriptSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False, auto_created=True, primary_key=True)),
                ('plugin', models.CharField(max_length=255)),
                ('historical', models.BooleanField(default=False)),
                ('recorded', models.DateTimeField(auto_now_add=True)),
                ('machine', models.ForeignKey(to='server.Machine')),
            ],
            options={
                'ordering': ['recorded', 'plugin'],
            },
        ),
        migrations.AddField(
            model_name='pluginscriptrow',
            name='submission',
            field=models.ForeignKey(to='server.PluginScriptSubmission'),
        ),
    ]
