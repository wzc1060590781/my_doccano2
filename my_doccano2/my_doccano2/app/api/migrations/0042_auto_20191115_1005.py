# Generated by Django 2.0.1 on 2019-11-15 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_algorithm_is_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='pic',
            field=models.ImageField(default='project/default.jpg', upload_to='project/'),
        ),
        migrations.AlterField(
            model_name='algorithm',
            name='is_delete',
            field=models.BooleanField(default=False, verbose_name='算法是否删除删除'),
        ),
    ]
