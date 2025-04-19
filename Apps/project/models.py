from django.db import models
from django.utils.translation import gettext_lazy as _
from Apps.core.models import BaseModel
from Apps.users.models import User
from Apps.entity.models import Organization
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

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

class ProjectSchedule(BaseModel):
    """
    Represents the schedule for a project, including estimated start and end dates
    """
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='schedule'
    )
    estimated_start_date = models.DateTimeField()
    estimated_end_date = models.DateTimeField()
    description = models.TextField(blank=True)
    is_baseline = models.BooleanField(default=False)
    progress = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text=_('Percentage of completion (0-100)')
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_all_schedules', 'Can view all project schedules'),
            ('manage_schedules', 'Can manage project schedules'),
        ]

    def __str__(self):
        return f"Schedule for {self.project.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate date range
        if self.estimated_start_date and self.estimated_end_date and self.estimated_start_date > self.estimated_end_date:
            raise ValidationError(_('Estimated start date must be before estimated end date'))
        
        # Validate project relation
        if self.project:
            # Check if schedule dates are within project dates
            if self.estimated_start_date < self.project.start_date:
                raise ValidationError(_('Schedule start date cannot be before project start date'))
            if self.estimated_end_date > self.project.end_date:
                raise ValidationError(_('Schedule end date cannot be after project end date'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_duration(self):
        """Return the duration of the schedule in days"""
        if self.estimated_start_date and self.estimated_end_date:
            return (self.estimated_end_date - self.estimated_start_date).days
        return 0

    def update_progress(self):
        """Update progress based on completed milestones"""
        total_milestones = self.milestones.count()
        if total_milestones > 0:
            completed_milestones = self.milestones.filter(status='completed').count()
            self.progress = int((completed_milestones / total_milestones) * 100)
            self.save(update_fields=['progress'])
        return self.progress

class ProjectPhase(BaseModel):
    """
    Represents a phase or stage in a project schedule
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schedule = models.ForeignKey(
        ProjectSchedule,
        on_delete=models.CASCADE,
        related_name='phases'
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    progress = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text=_('Percentage of completion (0-100)')
    )

    class Meta:
        ordering = ['order', 'start_date']
        permissions = [
            ('view_all_phases', 'Can view all project phases'),
            ('manage_phases', 'Can manage project phases'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate date range
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_('Start date must be before end date'))
        
        # Validate schedule relation
        if self.schedule:
            # Check if phase dates are within schedule dates
            if self.start_date < self.schedule.estimated_start_date:
                raise ValidationError(_('Phase start date cannot be before schedule start date'))
            if self.end_date > self.schedule.estimated_end_date:
                raise ValidationError(_('Phase end date cannot be after schedule end date'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_duration(self):
        """Return the duration of the phase in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    def update_progress(self):
        """Update progress based on completed milestones"""
        total_milestones = self.milestones.count()
        if total_milestones > 0:
            completed_milestones = self.milestones.filter(status='completed').count()
            self.progress = int((completed_milestones / total_milestones) * 100)
            self.save(update_fields=['progress'])
        return self.progress

class Milestone(BaseModel):
    """
    Represents a significant point or event in a project schedule
    """
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        DELAYED = 'delayed', _('Delayed')
        CANCELLED = 'cancelled', _('Cancelled')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schedule = models.ForeignKey(
        ProjectSchedule,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    phase = models.ForeignKey(
        ProjectPhase,
        on_delete=models.CASCADE,
        related_name='milestones',
        null=True,
        blank=True
    )
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date']
        permissions = [
            ('view_all_milestones', 'Can view all project milestones'),
            ('manage_milestones', 'Can manage project milestones'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate schedule relation
        if self.schedule:
            # Check if milestone due date is within schedule dates
            if self.due_date < self.schedule.estimated_start_date:
                raise ValidationError(_('Milestone due date cannot be before schedule start date'))
            if self.due_date > self.schedule.estimated_end_date:
                raise ValidationError(_('Milestone due date cannot be after schedule end date'))
        
        # Validate phase relation if provided
        if self.phase:
            # Check if milestone due date is within phase dates
            if self.due_date < self.phase.start_date:
                raise ValidationError(_('Milestone due date cannot be before phase start date'))
            if self.due_date > self.phase.end_date:
                raise ValidationError(_('Milestone due date cannot be after phase end date'))
            
            # Check if phase belongs to the same schedule
            if self.phase.schedule != self.schedule:
                raise ValidationError(_('Phase must belong to the same schedule as the milestone'))

    def save(self, *args, **kwargs):
        self.clean()
        
        # Set completion date if status is completed
        if self.status == self.Status.COMPLETED and not self.completion_date:
            self.completion_date = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completion_date = None
            
        super().save(*args, **kwargs)
        
        # Update progress of parent objects
        if self.phase:
            self.phase.update_progress()
        self.schedule.update_progress()

    def complete(self):
        """Mark milestone as completed"""
        self.status = self.Status.COMPLETED
        self.completion_date = timezone.now()
        self.save()
