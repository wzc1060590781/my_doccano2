# Generated by Django 2.0.1 on 2019-12-17 14:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0045_auto_20191216_1103'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='task',
            options={'verbose_name': '任务表'},
        ),
        migrations.AlterUniqueTogether(
            name='task',
            unique_together={('user', 'document')},
        ),
        migrations.AlterModelTable(
            name='task',
            table='tasks',
        ),
    ]
