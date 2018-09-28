

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0037_auto_20160310_1001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pluginscriptrow',
            name='pluginscript_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='level',
            field=models.CharField(default=b'RO', max_length=2, choices=[(
                b'SO', b'Stats Only'), (b'RO', b'Read Only'), (b'RW', b'Read Write'), (b'GA', b'Global Admin')]),
        ),
    ]
