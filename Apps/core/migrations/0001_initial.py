# Generated by Django 4.2.11 on 2025-04-10 06:52

import Apps.core.mixins
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_status', models.CharField(choices=[('pending', 'PENDING'), ('processing', 'PROCESSING'), ('completed', 'COMPLETED'), ('failed', 'FAILED')], default='pending', max_length=20)),
                ('task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('task_result', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('key', models.CharField(max_length=255, unique=True)),
                ('value', models.JSONField()),
                ('description', models.TextField(blank=True, null=True)),
                ('is_editable', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Configuration',
                'verbose_name_plural': 'Configurations',
                'ordering': ['key'],
            },
            bases=(Apps.core.mixins.ImportExportMixin, models.Model),
        ),
    ]
