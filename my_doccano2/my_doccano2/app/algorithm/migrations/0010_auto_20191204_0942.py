# Generated by Django 2.0.1 on 2019-12-04 09:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0044_delete_algorithm'),
        ('algorithm', '0009_remove_algorithm_algorithm_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlgorithmProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间')),
                ('model_url', models.CharField(max_length=200, null=True)),
                ('config', models.FileField(upload_to='configs/')),
                ('algorithm', models.ForeignKey(help_text='用户', on_delete=django.db.models.deletion.CASCADE, to='algorithm.Algorithm')),
                ('project', models.ForeignKey(help_text='项目', on_delete=django.db.models.deletion.CASCADE, to='api.Project')),
            ],
            options={
                'verbose_name': '算法项目表',
                'db_table': 'algorithm_project_tb',
            },
        ),
        migrations.AddField(
            model_name='algorithm',
            name='project',
            field=models.ManyToManyField(help_text='项目', through='algorithm.AlgorithmProject', to='api.Project'),
        ),
        migrations.AlterUniqueTogether(
            name='algorithmproject',
            unique_together={('project', 'algorithm')},
        ),
    ]
