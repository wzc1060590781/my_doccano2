# Generated by Django 2.0.1 on 2019-12-03 15:15

import algorithm.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('algorithm', '0009_remove_algorithm_algorithm_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='algorithm',
            name='algorithm_file',
            field=models.FileField(storage=algorithm.models.mystorage(), upload_to='algorithm/'),
        ),
    ]
