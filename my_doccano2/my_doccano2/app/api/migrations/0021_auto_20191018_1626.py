# Generated by Django 2.0.1 on 2019-10-18 16:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_auto_20191017_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotation',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='document',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_annoteated',
            field=models.BooleanField(default=False, help_text='是否被标注', verbose_name='文本是否已被标注'),
        ),
        migrations.AlterField(
            model_name='document',
            name='is_delete',
            field=models.BooleanField(default=False, help_text='是否被删除', verbose_name='文本是否被逻辑删除'),
        ),
        migrations.AlterField(
            model_name='document',
            name='project',
            field=models.ForeignKey(blank=True, help_text='所属项目', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='api.Project', verbose_name='所属项目'),
        ),
        migrations.AlterField(
            model_name='document',
            name='text',
            field=models.TextField(help_text='文书内容', verbose_name='文书内容'),
        ),
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(help_text='文档标题', max_length=100, null=True, verbose_name='文档标题'),
        ),
        migrations.AlterField(
            model_name='document',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='label',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='label',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='project',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.TextField(default='', help_text='项目描述信息'),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(help_text='项目名称', max_length=20, unique=True, verbose_name='项目名称'),
        ),
        migrations.AlterField(
            model_name='project',
            name='owner',
            field=models.ForeignKey(blank=True, help_text='项目管理者', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to=settings.AUTH_USER_MODEL, verbose_name='项目管理者'),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_type',
            field=models.CharField(choices=[('DocumentClassification', 'document classification'), ('SequenceLabeling', 'sequence labeling'), ('Seq2seq', 'sequence to sequence')], help_text='项目类型', max_length=30),
        ),
        migrations.AlterField(
            model_name='project',
            name='randomize_document_order',
            field=models.BooleanField(default=False, help_text='是否乱序', verbose_name='是否乱序'),
        ),
        migrations.AlterField(
            model_name='project',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='project',
            name='users',
            field=models.ManyToManyField(help_text='用户', through='api.Project_User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project_user',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='project_user',
            name='project',
            field=models.ForeignKey(help_text='项目', on_delete=django.db.models.deletion.CASCADE, to='api.Project'),
        ),
        migrations.AlterField(
            model_name='project_user',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='project_user',
            name='user',
            field=models.ForeignKey(help_text='用户', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='role',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True, help_text='创建时间', verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(help_text='角色名', max_length=20, unique=True, verbose_name='角色'),
        ),
        migrations.AlterField(
            model_name='role',
            name='update_time',
            field=models.DateTimeField(auto_now=True, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.ForeignKey(blank=True, help_text='角色', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='api.Role', verbose_name='角色'),
        ),
    ]
