from django.db import models
from django.utils.translation import gettext_lazy as _
from Apps.core.models import BaseModel
from Apps.users.models import User
from Apps.entity.models import Organization

class Project(BaseModel):
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        IN_PROGRESS = 'in_progress', _('In Progress')
        ON_HOLD = 'on_hold', _('On Hold')
        COMPLETED = 'completed', _('Completed')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_projects'
    )
    team_members = models.ManyToManyField(
        User,
        related_name='project_memberships'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_all_projects', 'Can view all projects'),
            ('manage_project_members', 'Can manage project members'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_('Start date must be before end date'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Task(BaseModel):
    class Status(models.TextChoices):
        TODO = 'todo', _('Todo')
        IN_PROGRESS = 'in_progress', _('In Progress')
        DONE = 'done', _('Done')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_tasks'
    )
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )

    class Meta:
        ordering = ['due_date', '-priority']
        permissions = [
            ('view_all_tasks', 'Can view all tasks'),
            ('manage_task_assignments', 'Can manage task assignments'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.parent_task and self.parent_task.project != self.project:
            raise ValidationError(_('Parent task must belong to the same project'))
        if self.due_date and self.project.end_date and self.due_date > self.project.end_date:
            raise ValidationError(_('Task due date cannot be after project end date'))

class ProjectTemplate(BaseModel):
    """
    Template for creating projects with predefined settings and tasks
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    estimated_duration = models.IntegerField(help_text=_('Estimated duration in days'))
    default_status = models.CharField(
        max_length=20,
        choices=Project.Status.choices,
        default=Project.Status.NEW
    )
    default_priority = models.CharField(
        max_length=20,
        choices=Project.Priority.choices,
        default=Project.Priority.MEDIUM
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='project_templates'
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_all_project_templates', 'Can view all project templates'),
            ('manage_project_templates', 'Can manage project templates'),
        ]

    def __str__(self):
        return self.title

class TaskTemplate(BaseModel):
    """
    Template for creating tasks with predefined settings
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    estimated_duration = models.IntegerField(help_text=_('Estimated duration in days'))
    default_status = models.CharField(
        max_length=20,
        choices=Task.Status.choices,
        default=Task.Status.TODO
    )
    default_priority = models.CharField(
        max_length=20,
        choices=Task.Priority.choices,
        default=Task.Priority.MEDIUM
    )
    project_template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.CASCADE,
        related_name='task_templates'
    )
    parent_task_template = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtask_templates'
    )
    order = models.PositiveIntegerField(default=0, help_text=_('Order of execution'))

    class Meta:
        ordering = ['order', 'created_at']
        permissions = [
            ('view_all_task_templates', 'Can view all task templates'),
            ('manage_task_templates', 'Can manage task templates'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.parent_task_template and self.parent_task_template.project_template != self.project_template:
            raise ValidationError(_('Parent task template must belong to the same project template'))
