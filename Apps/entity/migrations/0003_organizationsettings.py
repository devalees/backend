# Generated by Django 5.1.7 on 2025-04-05 17:35

import Apps.core.mixins
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entity', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationSettings',
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
                ('timezone', models.CharField(default='UTC', help_text='Organization timezone', max_length=50)),
                ('date_format', models.CharField(default='YYYY-MM-DD', help_text='Organization date format', max_length=20)),
                ('time_format', models.CharField(choices=[('12h', '12-hour'), ('24h', '24-hour')], default='24h', help_text='Organization time format', max_length=10)),
                ('language', models.CharField(default='en', help_text='Organization default language', max_length=10)),
                ('notification_preferences', models.JSONField(default=dict, help_text='Organization notification preferences')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='settings', to='entity.organization')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Organization Settings',
                'verbose_name_plural': 'Organization Settings',
            },
            bases=(Apps.core.mixins.ImportExportMixin, models.Model),
        ),
    ]
