# Generated by Django 2.0.1 on 2019-10-12 05:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_document_is_annoteated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='parents',
        ),
    ]
