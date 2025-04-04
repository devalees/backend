# Generated by Django 5.1.7 on 2025-04-04 10:45

import Apps.core.mixins
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0002_triggerexecution_triggermetrics_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(blank=True, max_length=100, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('extra_fields', models.JSONField(blank=True, null=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('task_status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20, verbose_name='Task Status')),
                ('task_result', models.JSONField(blank=True, null=True, verbose_name='Task Result')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Error Message')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='automation.workflow', verbose_name='Workflow')),
            ],
            options={
                'verbose_name': 'Task',
                'verbose_name_plural': 'Tasks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TaskDependency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_status', models.CharField(choices=[('pending', 'PENDING'), ('processing', 'PROCESSING'), ('completed', 'COMPLETED'), ('failed', 'FAILED')], default='pending', max_length=20)),
                ('task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('task_result', models.JSONField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('dependency_task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependents', to='automation.task', verbose_name='Dependency Task')),
                ('dependent_task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependencies', to='automation.task', verbose_name='Dependent Task')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Task Dependency',
                'verbose_name_plural': 'Task Dependencies',
            },
            bases=(Apps.core.mixins.ImportExportMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['name'], name='automation__name_fb22e5_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['task_status'], name='automation__task_st_b46276_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['created_at'], name='automation__created_48b376_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdependency',
            index=models.Index(fields=['dependent_task'], name='automation__depende_4e058d_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdependency',
            index=models.Index(fields=['dependency_task'], name='automation__depende_9306c1_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdependency',
            index=models.Index(fields=['created_at'], name='automation__created_0062f5_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='taskdependency',
            unique_together={('dependent_task', 'dependency_task')},
        ),
    ]
