# Generated by Django 2.0.1 on 2019-10-14 03:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_remove_user_mobile'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotations', to=settings.AUTH_USER_MODEL, verbose_name='打标签者'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='api.Document', verbose_name='所属文本'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='label',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotations', to='api.Label', verbose_name='标记'),
        ),
    ]
