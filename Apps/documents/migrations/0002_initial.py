# Generated by Django 5.1.7 on 2025-04-02 18:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='documentclassification',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='documents.documentclassification'),
        ),
        migrations.AddField(
            model_name='document',
            name='classification',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='documents.documentclassification'),
        ),
        migrations.AddIndex(
            model_name='documenttag',
            index=models.Index(fields=['name'], name='documents_d_name_aed49a_idx'),
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=models.ManyToManyField(blank=True, to='documents.documenttag'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='documents.document'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='merged_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='merged_from', to='documents.documentversion'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='parent_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='branches', to='documents.documentversion'),
        ),
        migrations.AddField(
            model_name='documentversion',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='documentclassification',
            index=models.Index(fields=['name'], name='documents_d_name_5dd23a_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['title'], name='documents_d_title_ccf306_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['status'], name='documents_d_status_07369e_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['created_at'], name='documents_d_created_3b0a51_idx'),
        ),
        migrations.AddIndex(
            model_name='documentversion',
            index=models.Index(fields=['document', 'version_number'], name='documents_d_documen_68fe34_idx'),
        ),
        migrations.AddIndex(
            model_name='documentversion',
            index=models.Index(fields=['is_current'], name='documents_d_is_curr_5ca7d4_idx'),
        ),
        migrations.AddIndex(
            model_name='documentversion',
            index=models.Index(fields=['branch_name'], name='documents_d_branch__f73081_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='documentversion',
            unique_together={('document', 'branch_name', 'version_number')},
        ),
    ]
