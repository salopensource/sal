

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0039_auto_20160707_0631'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='machine_model_friendly',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
    ]
