# Generated by Django 2.0.1 on 2019-11-06 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0040_auto_20191106_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='algorithm',
            name='is_delete',
            field=models.BooleanField(default=False),
        ),
    ]
