"""
Models for automation system.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from Apps.core.models import BaseModel
from Core.models.base import TaskAwareModel
from django.conf import settings
from django.utils import timezone
from typing import List, Set

User = get_user_model()

class Workflow(BaseModel):
    """
    Represents an automation workflow that can be triggered and executed.
    """
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    task_status = models.CharField(
        _('Task Status'),
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('error', 'Error')
        ],
        default='pending'
    )
    task_result = models.JSONField(_('Task Result'), null=True, blank=True)
    error_message = models.TextField(_('Error Message'), null=True, blank=True)
    last_run = models.DateTimeField(_('Last Run'), null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='workflows',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def clean(self):
        """Validate workflow data."""
        if not self.name:
            raise ValidationError(_('Workflow name is required'))
            
        if not self.created_by:
            raise ValidationError(_('Created by user is required'))

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'automation'
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

class Trigger(BaseModel):
    """
    Represents a trigger that can initiate a workflow.
    """
    TRIGGER_TYPES = [
        ('time', _('Time-based')),
        ('event', _('Event-based')),
        ('data', _('Data-based')),
    ]

    name = models.CharField(_('Name'), max_length=255)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='triggers',
        verbose_name=_('Workflow')
    )
    trigger_type = models.CharField(
        _('Trigger Type'),
        max_length=20,
        choices=TRIGGER_TYPES
    )
    conditions = models.JSONField(_('Conditions'), default=dict, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='triggers'
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    def clean(self):
        """Validate trigger data."""
        if not self.name:
            raise ValidationError(_('Trigger name is required'))
            
        if not self.workflow:
            raise ValidationError(_('Workflow is required'))
            
        if not self.trigger_type:
            raise ValidationError(_('Trigger type is required'))
            
        if not self.created_by:
            raise ValidationError(_('Created by user is required'))

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'automation'
        verbose_name = _('Trigger')
        verbose_name_plural = _('Triggers')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['trigger_type']),
            models.Index(fields=['is_active']),
        ]

class TriggerExecution(BaseModel):
    """
    Tracks individual trigger executions and their outcomes.
    """
    STATUS_CHOICES = [
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name=_('Trigger')
    )
    started_at = models.DateTimeField(_('Started At'))
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )
    execution_time = models.FloatField(_('Execution Time (seconds)'), null=True, blank=True)
    error_message = models.TextField(_('Error Message'), null=True, blank=True)

    def complete_execution(self, status='completed', error_message=None):
        """Complete the execution with the given status and calculate execution time."""
        self.completed_at = timezone.now()
        self.status = status
        self.error_message = error_message
        self.execution_time = (self.completed_at - self.started_at).total_seconds()
        self.save()

    @classmethod
    def cleanup_old_executions(cls, days=30):
        """Delete executions older than specified days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        old_executions = cls.objects.filter(started_at__lt=cutoff_date)
        count = old_executions.count()
        old_executions.delete()
        return count

    class Meta:
        app_label = 'automation'
        verbose_name = _('Trigger Execution')
        verbose_name_plural = _('Trigger Executions')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['trigger', 'status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['status']),
        ]

class TriggerMetrics(BaseModel):
    """
    Stores aggregated metrics for trigger monitoring.
    """
    trigger = models.OneToOneField(
        Trigger,
        on_delete=models.CASCADE,
        related_name='metrics',
        verbose_name=_('Trigger')
    )
    total_executions = models.IntegerField(_('Total Executions'), default=0)
    successful_executions = models.IntegerField(_('Successful Executions'), default=0)
    failed_executions = models.IntegerField(_('Failed Executions'), default=0)
    success_rate = models.FloatField(_('Success Rate (%)'), default=0.0)
    average_execution_time = models.FloatField(_('Average Execution Time (seconds)'), default=0.0)
    last_execution_status = models.CharField(_('Last Execution Status'), max_length=20, null=True)
    last_execution_time = models.DateTimeField(_('Last Execution Time'), null=True)

    @classmethod
    def calculate_metrics(cls, trigger):
        """Calculate and update metrics for a trigger."""
        executions = trigger.executions.all()
        total = executions.count()
        successful = executions.filter(status='completed').count()
        failed = executions.filter(status='failed').count()
        
        # Calculate success rate
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        # Calculate average execution time
        avg_time = executions.filter(
            execution_time__isnull=False
        ).aggregate(avg_time=models.Avg('execution_time'))['avg_time'] or 0.0
        
        # Get last execution info
        last_execution = executions.order_by('-started_at').first()
        
        metrics, _ = cls.objects.update_or_create(
            trigger=trigger,
            defaults={
                'total_executions': total,
                'successful_executions': successful,
                'failed_executions': failed,
                'success_rate': success_rate,
                'average_execution_time': avg_time,
                'last_execution_status': last_execution.status if last_execution else None,
                'last_execution_time': last_execution.completed_at if last_execution else None,
            }
        )
        return metrics

    @staticmethod
    def check_trigger_health(trigger):
        """Check the health status of a trigger based on recent executions."""
        recent_executions = trigger.executions.filter(
            started_at__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        total_recent = recent_executions.count()
        recent_failures = recent_executions.filter(status='failed').count()
        
        if total_recent > 0:
            success_rate = ((total_recent - recent_failures) / total_recent) * 100
        else:
            success_rate = 100.0
        
        # Determine health status
        if success_rate >= 90:
            status = 'healthy'
        elif success_rate >= 70:
            status = 'warning'
        else:
            status = 'critical'
            
        return {
            'status': status,
            'success_rate': success_rate,
            'recent_failures': recent_failures,
            'total_executions_24h': total_recent
        }

    class Meta:
        app_label = 'automation'
        verbose_name = _('Trigger Metrics')
        verbose_name_plural = _('Trigger Metrics')
        indexes = [
            models.Index(fields=['trigger']),
            models.Index(fields=['success_rate']),
            models.Index(fields=['last_execution_time']),
        ]

class Action(BaseModel):
    """
    Represents an action that can be executed by a workflow.
    """
    ACTION_TYPES = [
        ('email', _('Send Email')),
        ('notification', _('Send Notification')),
        ('webhook', _('Call Webhook')),
        ('task', _('Create Task')),
    ]

    name = models.CharField(_('Name'), max_length=255)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_('Workflow')
    )
    action_type = models.CharField(
        _('Action Type'),
        max_length=20,
        choices=ACTION_TYPES
    )
    configuration = models.JSONField(_('Configuration'), default=dict, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'automation'
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['action_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate action data."""
        if not self.name:
            raise ValidationError(_('Action name is required'))
            
        if not self.workflow:
            raise ValidationError(_('Workflow is required'))
            
        if not self.action_type:
            raise ValidationError(_('Action type is required'))
            
        if not self.created_by:
            raise ValidationError(_('Created by user is required'))

class Rule(BaseModel):
    """
    Represents a rule that links a trigger to an action in a workflow.
    """
    name = models.CharField(_('Name'), max_length=255)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name=_('Workflow')
    )
    trigger = models.ForeignKey(
        Trigger,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name=_('Trigger')
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name='rules',
        verbose_name=_('Action')
    )
    conditions = models.JSONField(_('Conditions'), default=dict, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'automation'
        verbose_name = _('Rule')
        verbose_name_plural = _('Rules')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate rule data."""
        if not self.name:
            raise ValidationError(_('Rule name is required'))
            
        if not self.workflow:
            raise ValidationError(_('Workflow is required'))
            
        if not self.trigger:
            raise ValidationError(_('Trigger is required'))
            
        if not self.action:
            raise ValidationError(_('Action is required'))
            
        if not self.created_by:
            raise ValidationError(_('Created by user is required'))
            
        # Validate that trigger and action belong to the same workflow
        if self.trigger.workflow_id != self.workflow_id:
            raise ValidationError({'trigger': _('Trigger must belong to the same workflow')})
            
        if self.action.workflow_id != self.workflow_id:
            raise ValidationError({'action': _('Action must belong to the same workflow')})

class RuleTemplate(TaskAwareModel):
    """
    Represents a template for creating rules with predefined conditions and configurations.
    Templates can be used to create consistent rules across different workflows.
    """
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    conditions = models.JSONField(_('Conditions'), default=dict)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rule_templates',
        verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='%(class)s_updated',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Rule Template')
        verbose_name_plural = _('Rule Templates')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active'])
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError({'name': _('Name is required')})
        
        if not self.conditions:
            raise ValidationError({'conditions': _('Conditions are required')})
            
        if not isinstance(self.conditions, dict):
            raise ValidationError({'conditions': _('Conditions must be a dictionary')})

    def create_rule(self, **kwargs):
        """Create a new rule from this template."""
        if not self.is_active:
            raise ValidationError(_("Cannot create rule from inactive template"))
        
        rule = Rule.objects.create(
            name=f"Rule from template: {self.name}",
            conditions=self.conditions.copy(),
            created_by=self.created_by,
            **kwargs
        )
        return rule

    def update_rules(self):
        """Update all rules created from this template with current conditions."""
        if not self.is_active:
            return
            
        Rule.objects.filter(
            name__startswith=f"Rule from template: {self.name}"
        ).update(conditions=self.conditions)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class WorkflowTemplate(models.Model):
    """Model for storing reusable workflow templates"""
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    configuration = models.JSONField(_('Configuration'))
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_workflow_templates',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Workflow Template')
        verbose_name_plural = _('Workflow Templates')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the workflow template configuration"""
        if not self.configuration:
            raise ValidationError({'configuration': _('Configuration is required')})
        
        if not isinstance(self.configuration, dict):
            raise ValidationError({'configuration': _('Configuration must be a JSON object')})
        
        if 'nodes' not in self.configuration:
            raise ValidationError({'configuration': _('Configuration must include nodes')})
        
        if not isinstance(self.configuration['nodes'], list):
            raise ValidationError({'configuration': _('Nodes must be a list')})

class Node(models.Model):
    """Model for nodes in the visual workflow"""
    NODE_TYPES = [
        ('trigger', _('Trigger')),
        ('action', _('Action')),
        ('condition', _('Condition')),
    ]

    name = models.CharField(_('Name'), max_length=255)
    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name='nodes',
        verbose_name=_('Workflow')
    )
    node_type = models.CharField(_('Node Type'), max_length=20, choices=NODE_TYPES)
    configuration = models.JSONField(_('Configuration'))
    position_x = models.IntegerField(_('Position X'), default=0)
    position_y = models.IntegerField(_('Position Y'), default=0)
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_nodes',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Node')
        verbose_name_plural = _('Nodes')
        ordering = ['workflow', 'created_at']

    def __str__(self):
        return f"{self.name} ({self.get_node_type_display()})"

    def clean(self):
        """Validate the node configuration"""
        if not self.configuration:
            raise ValidationError({'configuration': _('Configuration is required')})
        
        if not isinstance(self.configuration, dict):
            raise ValidationError({'configuration': _('Configuration must be a JSON object')})
        
        # Validate configuration based on node type
        if self.node_type == 'trigger':
            if 'trigger_type' not in self.configuration:
                raise ValidationError({'configuration': _('Trigger configuration must include trigger_type')})
        elif self.node_type == 'action':
            if 'action_type' not in self.configuration:
                raise ValidationError({'configuration': _('Action configuration must include action_type')})

class Connection(models.Model):
    """Model for connections between nodes in the visual workflow"""
    name = models.CharField(_('Name'), max_length=255, blank=True)
    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name='connections',
        verbose_name=_('Workflow')
    )
    source_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='outgoing_connections',
        verbose_name=_('Source Node')
    )
    target_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='incoming_connections',
        verbose_name=_('Target Node')
    )
    configuration = models.JSONField(_('Configuration'))
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_connections',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Connection')
        verbose_name_plural = _('Connections')
        ordering = ['workflow', 'created_at']

    def __str__(self):
        return f"Connection: {self.source_node.name} → {self.target_node.name}"

    def clean(self):
        """Validate the connection"""
        if self.source_node == self.target_node:
            raise ValidationError(_('A node cannot connect to itself'))

        if self.source_node.workflow != self.workflow or self.target_node.workflow != self.workflow:
            raise ValidationError(_('Source and target nodes must belong to the same workflow'))

        if not self.configuration:
            raise ValidationError({'configuration': _('Configuration is required')})

        if not isinstance(self.configuration, dict):
            raise ValidationError({'configuration': _('Configuration must be a JSON object')})

class TaskDependency(BaseModel):
    """
    Represents a dependency between two tasks.
    The dependent task cannot start until the dependency task is completed.
    """
    dependent_task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='dependencies',
        verbose_name=_('Dependent Task')
    )
    dependency_task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='dependents',
        verbose_name=_('Dependency Task')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        verbose_name = _('Task Dependency')
        verbose_name_plural = _('Task Dependencies')
        unique_together = ('dependent_task', 'dependency_task')
        indexes = [
            models.Index(fields=['dependent_task']),
            models.Index(fields=['dependency_task']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        """Validate task dependency."""
        if self.dependent_task == self.dependency_task:
            raise ValidationError(_('A task cannot depend on itself'))
        
        # Check for circular dependencies
        if self._creates_circular_dependency():
            raise ValidationError(_('This dependency would create a circular reference'))

    def _creates_circular_dependency(self) -> bool:
        """
        Check if adding this dependency would create a circular reference.
        Returns True if a circular dependency would be created, False otherwise.
        """
        visited: Set[int] = set()
        
        def check_dependencies(task_id: int) -> bool:
            if task_id in visited:
                return True
            visited.add(task_id)
            
            # Get all dependencies of the current task
            deps = list(TaskDependency.objects.filter(dependent_task_id=task_id).values_list('dependency_task_id', flat=True))
            
            # Include the new dependency if we're checking the dependent task
            if task_id == self.dependent_task_id and not self._state.adding:
                deps.append(self.dependency_task_id)
            
            for dep_id in deps:
                # If we find the original dependent task in the chain, we have a circle
                if dep_id == self.dependent_task_id:
                    return True
                if check_dependencies(dep_id):
                    return True
            
            visited.remove(task_id)
            return False
        
        # Start checking from the dependency task
        return check_dependencies(self.dependency_task_id)

    def __str__(self):
        return f"{self.dependent_task} depends on {self.dependency_task}"

class Task(TaskAwareModel):
    """
    Represents a task that can be executed as part of a workflow.
    Tasks can have dependencies on other tasks.
    """
    name = models.CharField(_('Name'), max_length=255)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Workflow')
    )
    task_status = models.CharField(
        _('Task Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('completed', _('Completed')),
            ('failed', _('Failed'))
        ],
        default='pending'
    )
    task_result = models.JSONField(_('Task Result'), null=True, blank=True)
    error_message = models.TextField(_('Error Message'), null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        app_label = 'automation'
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['task_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_task_status_display()})"

    def clean(self):
        """Validate task data."""
        if not self.name:
            raise ValidationError(_('Task name is required'))
            
        if not self.workflow:
            raise ValidationError(_('Workflow is required'))
            
        if not self.created_by:
            raise ValidationError(_('Created by user is required'))

    def are_dependencies_satisfied(self) -> bool:
        """
        Check if all dependencies for this task are satisfied.
        A task's dependencies are satisfied when all dependency tasks are completed.
        """
        incomplete_deps = self.dependencies.filter(
            dependency_task__task_status__in=['pending', 'processing', 'failed']
        )
        return not incomplete_deps.exists()

    def get_dependency_chain(self) -> List['Task']:
        """
        Get the full chain of dependencies for this task in order of execution.
        Returns a list of tasks in the order they need to be executed.
        """
        chain = []
        visited = set()

        def build_chain(task):
            # Get all direct dependencies
            deps = task.dependencies.all()
            for dep in deps:
                dependency = dep.dependency_task
                if dependency.id not in visited:
                    visited.add(dependency.id)
                    # Recursively build chain for this dependency
                    build_chain(dependency)
                    chain.append(dependency)

        build_chain(self)
        return chain

    @property
    def task_config(self):
        """Return task configuration for TaskAwareModel."""
        return type('TaskConfig', (), {
            'status_field': 'task_status',
            'result_field': 'task_result',
            'error_field': 'error_message',
        })
