# Generated by Django 5.1.7 on 2025-04-04 11:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0005_reporttemplate_reportschedule_report_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_reports', models.IntegerField(default=0, verbose_name='Total Reports')),
                ('successful_reports', models.IntegerField(default=0, verbose_name='Successful Reports')),
                ('failed_reports', models.IntegerField(default=0, verbose_name='Failed Reports')),
                ('success_rate', models.FloatField(default=0.0, verbose_name='Success Rate (%)')),
                ('average_generation_time', models.FloatField(default=0.0, verbose_name='Average Generation Time (seconds)')),
                ('min_generation_time', models.FloatField(null=True, verbose_name='Minimum Generation Time (seconds)')),
                ('max_generation_time', models.FloatField(null=True, verbose_name='Maximum Generation Time (seconds)')),
                ('daily_average', models.FloatField(default=0.0, verbose_name='Daily Average Reports')),
                ('peak_usage_day', models.DateField(null=True, verbose_name='Peak Usage Day')),
                ('peak_daily_count', models.IntegerField(default=0, verbose_name='Peak Daily Count')),
                ('total_executions', models.IntegerField(default=0, verbose_name='Total Schedule Executions')),
                ('successful_executions', models.IntegerField(default=0, verbose_name='Successful Schedule Executions')),
                ('execution_success_rate', models.FloatField(default=0.0, verbose_name='Schedule Success Rate (%)')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('template', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='automation.reporttemplate', verbose_name='Template')),
            ],
            options={
                'verbose_name': 'Report Analytics',
                'verbose_name_plural': 'Report Analytics',
                'indexes': [models.Index(fields=['template'], name='automation__templat_95ee0b_idx'), models.Index(fields=['last_updated'], name='automation__last_up_8dbf0f_idx')],
            },
        ),
    ]
