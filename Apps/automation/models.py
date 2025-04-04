"""
Models for automation system.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from Apps.core.models import BaseModel

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
