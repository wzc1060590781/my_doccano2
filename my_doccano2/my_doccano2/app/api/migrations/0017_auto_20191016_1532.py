# Generated by Django 2.0.1 on 2019-10-16 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_auto_20191016_1531'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'ordering': ['-create_time'], 'verbose_name': '文书表'},
        ),
    ]
