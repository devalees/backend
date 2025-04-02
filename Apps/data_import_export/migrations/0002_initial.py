# Generated by Django 5.1.7 on 2025-04-02 18:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('data_import_export', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='importexportconfig',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_import_export_configs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='importexportconfig',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_import_export_configs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='importexportlog',
            name='config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data_import_export.importexportconfig'),
        ),
        migrations.AddField(
            model_name='importexportlog',
            name='performed_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='testmodel',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_test_models', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='testmodel',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_test_models', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='importexportconfig',
            unique_together={('name', 'content_type')},
        ),
        migrations.AddIndex(
            model_name='importexportlog',
            index=models.Index(fields=['-created_at'], name='data_import_created_9fb6a0_idx'),
        ),
        migrations.AddIndex(
            model_name='importexportlog',
            index=models.Index(fields=['performed_by'], name='data_import_perform_ab5871_idx'),
        ),
    ]
