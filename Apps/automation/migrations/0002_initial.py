# Generated by Django 4.2.11 on 2025-04-10 06:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('automation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowtemplate',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_workflow_templates', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='workflow',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='triggermetrics',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='triggermetrics',
            name='trigger',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='automation.trigger', verbose_name='Trigger'),
        ),
        migrations.AddField(
            model_name='triggermetrics',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='triggerexecution',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='triggerexecution',
            name='trigger',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='automation.trigger', verbose_name='Trigger'),
        ),
        migrations.AddField(
            model_name='triggerexecution',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='trigger',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='triggers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='trigger',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='trigger',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='triggers', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddField(
            model_name='taskdependency',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='taskdependency',
            name='dependency_task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependents', to='automation.task', verbose_name='Dependency Task'),
        ),
        migrations.AddField(
            model_name='taskdependency',
            name='dependent_task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dependencies', to='automation.task', verbose_name='Dependent Task'),
        ),
        migrations.AddField(
            model_name='taskdependency',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='task',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_tasks', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='task',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddField(
            model_name='ruletemplate',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rule_templates', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='ruletemplate',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rule',
            name='action',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='automation.action', verbose_name='Action'),
        ),
        migrations.AddField(
            model_name='rule',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rule',
            name='trigger',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='automation.trigger', verbose_name='Trigger'),
        ),
        migrations.AddField(
            model_name='rule',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rule',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddField(
            model_name='reporttemplate',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='report_templates', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='reportschedule',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='report_schedules', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='reportschedule',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='schedules', to='automation.reporttemplate', verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='reportanalytics',
            name='template',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='automation.reporttemplate', verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='report',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reports', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='report',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reports', to='automation.reporttemplate', verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='node',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_nodes', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='node',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nodes', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddField(
            model_name='connection',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_connections', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AddField(
            model_name='connection',
            name='source_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_connections', to='automation.node', verbose_name='Source Node'),
        ),
        migrations.AddField(
            model_name='connection',
            name='target_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_connections', to='automation.node', verbose_name='Target Node'),
        ),
        migrations.AddField(
            model_name='connection',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connections', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddField(
            model_name='action',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='action',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='action',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='automation.workflow', verbose_name='Workflow'),
        ),
        migrations.AddIndex(
            model_name='workflow',
            index=models.Index(fields=['name'], name='automation__name_0442ef_idx'),
        ),
        migrations.AddIndex(
            model_name='workflow',
            index=models.Index(fields=['is_active'], name='automation__is_acti_ac172e_idx'),
        ),
        migrations.AddIndex(
            model_name='triggermetrics',
            index=models.Index(fields=['trigger'], name='automation__trigger_72d529_idx'),
        ),
        migrations.AddIndex(
            model_name='triggermetrics',
            index=models.Index(fields=['success_rate'], name='automation__success_2cbb04_idx'),
        ),
        migrations.AddIndex(
            model_name='triggermetrics',
            index=models.Index(fields=['last_execution_time'], name='automation__last_ex_f783fc_idx'),
        ),
        migrations.AddIndex(
            model_name='triggerexecution',
            index=models.Index(fields=['trigger', 'status'], name='automation__trigger_e8cad2_idx'),
        ),
        migrations.AddIndex(
            model_name='triggerexecution',
            index=models.Index(fields=['started_at'], name='automation__started_135387_idx'),
        ),
        migrations.AddIndex(
            model_name='triggerexecution',
            index=models.Index(fields=['status'], name='automation__status_a1a666_idx'),
        ),
        migrations.AddIndex(
            model_name='trigger',
            index=models.Index(fields=['name'], name='automation__name_1f11c7_idx'),
        ),
        migrations.AddIndex(
            model_name='trigger',
            index=models.Index(fields=['trigger_type'], name='automation__trigger_d1ea29_idx'),
        ),
        migrations.AddIndex(
            model_name='trigger',
            index=models.Index(fields=['is_active'], name='automation__is_acti_0211bd_idx'),
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
            model_name='ruletemplate',
            index=models.Index(fields=['name'], name='automation__name_4bf580_idx'),
        ),
        migrations.AddIndex(
            model_name='ruletemplate',
            index=models.Index(fields=['is_active'], name='automation__is_acti_9c220a_idx'),
        ),
        migrations.AddIndex(
            model_name='rule',
            index=models.Index(fields=['name'], name='automation__name_0b4d09_idx'),
        ),
        migrations.AddIndex(
            model_name='rule',
            index=models.Index(fields=['is_active'], name='automation__is_acti_e15132_idx'),
        ),
        migrations.AddIndex(
            model_name='reporttemplate',
            index=models.Index(fields=['name'], name='automation__name_3b3ad5_idx'),
        ),
        migrations.AddIndex(
            model_name='reporttemplate',
            index=models.Index(fields=['created_at'], name='automation__created_d6d530_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['name'], name='automation__name_29e362_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['is_active'], name='automation__is_acti_a69f58_idx'),
        ),
        migrations.AddIndex(
            model_name='reportschedule',
            index=models.Index(fields=['next_run'], name='automation__next_ru_ef3b17_idx'),
        ),
        migrations.AddIndex(
            model_name='reportanalytics',
            index=models.Index(fields=['template'], name='automation__templat_95ee0b_idx'),
        ),
        migrations.AddIndex(
            model_name='reportanalytics',
            index=models.Index(fields=['last_updated'], name='automation__last_up_8dbf0f_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['name'], name='automation__name_f193fe_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['created_at'], name='automation__created_9f9fb4_idx'),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['generated_at'], name='automation__generat_661c39_idx'),
        ),
        migrations.AddIndex(
            model_name='action',
            index=models.Index(fields=['name'], name='automation__name_26577f_idx'),
        ),
        migrations.AddIndex(
            model_name='action',
            index=models.Index(fields=['action_type'], name='automation__action__2246a3_idx'),
        ),
        migrations.AddIndex(
            model_name='action',
            index=models.Index(fields=['is_active'], name='automation__is_acti_f437d2_idx'),
        ),
    ]
