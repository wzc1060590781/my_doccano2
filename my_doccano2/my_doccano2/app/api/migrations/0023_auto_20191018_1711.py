# Generated by Django 2.0.1 on 2019-10-18 17:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_auto_20191018_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project_user',
            name='project',
            field=models.ForeignKey(help_text='项目', on_delete=django.db.models.deletion.CASCADE, related_name='users_in_project', to='api.Project'),
        ),
        migrations.AlterField(
            model_name='project_user',
            name='user',
            field=models.ForeignKey(help_text='用户', on_delete=django.db.models.deletion.CASCADE, related_name='project_contains_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
