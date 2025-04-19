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
    estimated_hours = models.DecimalField(
        _('Estimated Hours'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
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
    
    @property
    def logged_hours(self):
        """Calculate total hours logged for this project"""
        from django.db.models import Sum
        from Apps.time_management.models import TimeEntry
        
        return TimeEntry.objects.filter(project=self).aggregate(total=Sum('hours'))['total'] or 0
    
    @property
    def hours_variance(self):
        """Calculate variance between estimated and actual hours"""
        return self.estimated_hours - self.logged_hours
    
    @property
    def progress_percentage(self):
        """Calculate progress based on logged time"""
        if not self.estimated_hours:
            # Try to get estimated hours from tasks
            from django.db.models import Sum
            task_hours = self.tasks.aggregate(total=Sum('estimated_hours'))['total'] or 0
            
            if task_hours > 0:
                return min(100, int((self.logged_hours / task_hours) * 100))
            
            # If we still don't have estimates, check schedule
            if hasattr(self, 'schedule') and self.schedule.estimated_hours:
                return min(100, int((self.logged_hours / self.schedule.estimated_hours) * 100))
                
            return 0
            
        return min(100, int((self.logged_hours / self.estimated_hours) * 100))
    
    def get_time_entries_by_user(self):
        """Get time entries grouped by user"""
        from django.db.models import Sum
        from Apps.time_management.models import TimeEntry
        
        return TimeEntry.objects.filter(project=self).values(
            'user__username', 'user__id'
        ).annotate(
            total_hours=Sum('hours')
        ).order_by('-total_hours')
    
    def get_time_entries_by_task(self):
        """Get time entries grouped by task"""
        from django.db.models import Sum
        from Apps.time_management.models import TimeEntry
        
        return TimeEntry.objects.filter(
            project=self, 
            task__isnull=False
        ).values(
            'task__title', 'task__id'
        ).annotate(
            total_hours=Sum('hours')
        ).order_by('-total_hours')
    
    def get_time_entries_by_phase(self):
        """Get time entries grouped by project phase"""
        from django.db.models import Sum
        from Apps.time_management.models import TimeEntry
        
        return TimeEntry.objects.filter(
            project=self, 
            project_phase__isnull=False
        ).values(
            'project_phase__name', 'project_phase__id'
        ).annotate(
            total_hours=Sum('hours')
        ).order_by('-total_hours')
    
    def get_time_entries_by_date(self):
        """Get time entries grouped by date"""
        from django.db.models import Sum
        from django.db.models.functions import TruncDate
        from Apps.time_management.models import TimeEntry
        
        return TimeEntry.objects.filter(project=self).annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            total_hours=Sum('hours')
        ).order_by('date')
    
    def generate_time_report(self, start_date=None, end_date=None):
        """Generate a comprehensive time report for the project"""
        from django.db.models import Sum, Count, F, ExpressionWrapper, fields
        from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
        from Apps.time_management.models import TimeEntry
        
        # Filter time entries by date range if provided
        query = TimeEntry.objects.filter(project=self)
        if start_date:
            query = query.filter(start_time__gte=start_date)
        if end_date:
            query = query.filter(end_time__lte=end_date)
        
        # Basic metrics
        total_entries = query.count()
        total_hours = query.aggregate(total=Sum('hours'))['total'] or 0
        
        # Group by user
        by_user = query.values(
            'user__username', 'user__id'
        ).annotate(
            total_hours=Sum('hours'),
            entry_count=Count('id')
        ).order_by('-total_hours')
        
        # Group by task
        by_task = query.filter(task__isnull=False).values(
            'task__title', 'task__id'
        ).annotate(
            total_hours=Sum('hours'),
            entry_count=Count('id')
        ).order_by('-total_hours')
        
        # Group by date for timeline
        timeline_daily = query.annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            total_hours=Sum('hours')
        ).order_by('date')
        
        # Group by week
        timeline_weekly = query.annotate(
            week=TruncWeek('start_time')
        ).values('week').annotate(
            total_hours=Sum('hours')
        ).order_by('week')
        
        # Group by month
        timeline_monthly = query.annotate(
            month=TruncMonth('start_time')
        ).values('month').annotate(
            total_hours=Sum('hours')
        ).order_by('month')
        
        # Calculate billable vs non-billable
        billable_hours = query.filter(is_billable=True).aggregate(total=Sum('hours'))['total'] or 0
        non_billable_hours = total_hours - billable_hours
        
        return {
            'total_entries': total_entries,
            'total_hours': total_hours,
            'by_user': list(by_user),
            'by_task': list(by_task),
            'timeline_daily': list(timeline_daily),
            'timeline_weekly': list(timeline_weekly),
            'timeline_monthly': list(timeline_monthly),
            'billable_hours': billable_hours,
            'non_billable_hours': non_billable_hours,
            'billable_percentage': (billable_hours / total_hours * 100) if total_hours > 0 else 0
        }

    def delete(self, *args, **kwargs):
        """
        Override delete method to handle related objects properly.
        """
        # Delete related documents
        from Apps.document.models import Document
        Document.objects.filter(project=self).delete()
        
        # Delete related time entries
        from Apps.time_management.models import TimeEntry
        TimeEntry.objects.filter(project=self).delete()
        
        # Delete related discussions and attachments
        discussions = ProjectDiscussion.objects.filter(project=self)
        DiscussionAttachment.objects.filter(discussion__in=discussions).delete()
        DiscussionNotification.objects.filter(discussion__in=discussions).delete()
        discussions.delete()
        
        # Delete related events
        from Apps.event.models import Event
        Event.objects.filter(project=self).delete()
        
        # Delete the project
        super().delete(*args, **kwargs)

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
    
    # New fields for time management integration
    estimated_hours = models.DecimalField(
        _('Estimated Hours'),
        max_digits=7,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
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
            
    @property
    def logged_hours(self):
        """Calculate total hours logged for this task"""
        from django.db.models import Sum
        return self.time_entries.aggregate(total=Sum('hours'))['total'] or 0
        
    @property
    def hours_variance(self):
        """Calculate the variance between estimated and actual hours"""
        return self.estimated_hours - self.logged_hours
        
    @property
    def progress_percentage(self):
        """Calculate the task completion percentage based on logged hours"""
        if not self.estimated_hours:
            return 0
        return min(100, (self.logged_hours / self.estimated_hours) * 100)
        
    def update_status_based_on_progress(self):
        """Update task status based on logged time progress"""
        if self.progress_percentage >= 100 and self.status != self.Status.DONE:
            self.status = self.Status.DONE
            self.save(update_fields=['status'])
        elif self.progress_percentage > 0 and self.status == self.Status.TODO:
            self.status = self.Status.IN_PROGRESS
            self.save(update_fields=['status'])

    def delete(self, *args, **kwargs):
        """
        Override delete method to handle related objects properly.
        """
        # Delete related time entries
        from Apps.time_management.models import TimeEntry
        TimeEntry.objects.filter(task=self).delete()
        
        # Delete the task
        super().delete(*args, **kwargs)

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
    estimated_hours = models.DecimalField(
        _('Estimated Hours'),
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
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
        """
        Calculate the duration of the schedule in days
        """
        return (self.estimated_end_date - self.estimated_start_date).days + 1

    def update_progress(self):
        """
        Update progress based on phases, milestones, and time entries
        """
        # Get all phases for this schedule
        phases = self.phases.all()
        
        if not phases.exists():
            # If no phases, calculate progress from tasks and time entries
            self.calculate_progress_from_time_entries()
        else:
            # Calculate weighted progress from phases
            total_weight = sum(phase.estimated_hours or 1 for phase in phases)
            weighted_progress = sum(
                phase.progress * (phase.estimated_hours or 1) / total_weight 
                for phase in phases
            )
            
            self.progress = int(weighted_progress)
            self.save(update_fields=['progress'])
        
        return self.progress
    
    def calculate_progress_from_time_entries(self):
        """
        Calculate progress based on time entries across all tasks in the project
        """
        from django.db.models import Sum
        
        # Get estimated hours from tasks
        tasks = self.project.tasks.all()
        total_estimated = tasks.aggregate(total=Sum('estimated_hours'))['total'] or 0
        
        if total_estimated == 0:
            # If no task estimates, use schedule estimated hours
            total_estimated = self.estimated_hours
            
            # If still no estimate, can't calculate progress
            if total_estimated == 0:
                return
        
        # Get time entries for all tasks in the project
        total_logged = self.get_total_logged_hours()
        
        # Calculate progress
        progress_percentage = min(100, int((total_logged / total_estimated) * 100))
        
        # Update progress
        self.progress = progress_percentage
        self.save(update_fields=['progress'])
        
        return self.progress
    
    def get_total_logged_hours(self):
        """
        Get total hours logged for all tasks in the project
        """
        from django.db.models import Sum
        
        # Aggregate hours from all time entries for this project
        time_entries_sum = TimeEntry.objects.filter(
            project=self.project
        ).aggregate(total=Sum('hours'))['total'] or 0
        
        return time_entries_sum
        
    def get_burndown_data(self):
        """
        Calculate burndown chart data based on time entries
        """
        from django.db.models import Sum
        from django.db.models.functions import TruncDate
        
        # Get total estimated hours
        tasks = self.project.tasks.all()
        total_estimated = tasks.aggregate(total=Sum('estimated_hours'))['total'] or self.estimated_hours or 0
        
        if total_estimated == 0:
            return []
            
        # Get time entries grouped by day
        daily_hours = TimeEntry.objects.filter(
            project=self.project,
            start_time__gte=self.estimated_start_date,
            start_time__lte=self.estimated_end_date
        ).annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            daily_hours=Sum('hours')
        ).order_by('date')
        
        # Calculate remaining work
        remaining = [{'date': self.estimated_start_date.date(), 'remaining': total_estimated}]
        
        current_remaining = total_estimated
        for day_data in daily_hours:
            current_remaining -= day_data['daily_hours']
            remaining.append({
                'date': day_data['date'],
                'remaining': max(0, current_remaining)
            })
            
        return remaining
    
    def get_time_variance(self):
        """
        Calculate variance between estimated and actual time
        """
        total_estimated = self.estimated_hours
        total_logged = self.get_total_logged_hours()
        
        variance = total_estimated - total_logged
        variance_percentage = (variance / total_estimated) * 100 if total_estimated else 0
        
        return {
            'estimated_hours': total_estimated,
            'logged_hours': total_logged,
            'variance_hours': variance,
            'variance_percentage': variance_percentage
        }

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
    estimated_hours = models.DecimalField(
        _('Estimated Hours'),
        max_digits=7,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['order', 'start_date']
        permissions = [
            ('view_all_phases', 'Can view all project phases'),
            ('manage_phases', 'Can manage project phases'),
        ]

    def __str__(self):
        return f"{self.name} - {self.schedule.project.title}"

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
        """
        Calculate the duration of the phase in days
        """
        return (self.end_date - self.start_date).days + 1

    def update_progress(self):
        """Update phase progress based on logged time"""
        if self.estimated_hours > 0:
            from django.db.models import Sum
            logged_hours = self.time_entries.aggregate(total=Sum('hours'))['total'] or 0
            time_based_progress = min(100, int((logged_hours / self.estimated_hours) * 100))
            
            # Update progress field
            self.progress = time_based_progress
            self.save(update_fields=['progress'])
            
            # Update schedule progress
            self.schedule.update_progress()
        
        return self.progress
    
    @property
    def logged_hours(self):
        """Calculate total hours logged for this phase"""
        from django.db.models import Sum
        return self.time_entries.aggregate(total=Sum('hours'))['total'] or 0
        
    @property
    def hours_variance(self):
        """Calculate the variance between estimated and actual hours"""
        return self.estimated_hours - self.logged_hours
    
    def get_time_entries_by_date(self):
        """Group time entries by date for this phase"""
        from django.db.models import Sum
        from django.db.models.functions import TruncDate
        
        return self.time_entries.annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            total_hours=Sum('hours')
        ).order_by('date')

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
    completion_percentage = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        help_text=_('Percentage of completion (0-100)')
    )
    estimated_hours = models.DecimalField(
        _('Estimated Hours'), 
        max_digits=7, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['due_date']
        permissions = [
            ('view_all_milestones', 'Can view all milestones'),
            ('manage_milestones', 'Can manage milestones'),
        ]

    def __str__(self):
        return f"{self.name} - {self.schedule.project.title}"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate due date
        if self.schedule and self.due_date > self.schedule.estimated_end_date:
            raise ValidationError(_('Milestone due date cannot be after schedule end date'))
            
        # Validate phase relation
        if self.phase:
            # Check if phase belongs to the same schedule
            if self.phase.schedule != self.schedule:
                raise ValidationError(_('Phase must belong to the same schedule'))
                
            # Check if milestone due date is within phase dates
            if self.due_date < self.phase.start_date or self.due_date > self.phase.end_date:
                raise ValidationError(_('Milestone due date must be within phase dates'))
        
        # Validate completion date
        if self.completion_date and self.completion_date > timezone.now():
            raise ValidationError(_('Completion date cannot be in the future'))

    def save(self, *args, **kwargs):
        # Automatically set completion date when status is set to completed
        if self.status == self.Status.COMPLETED and not self.completion_date:
            self.completion_date = timezone.now()
            
        # Check if status is being set to completed
        status_changed_to_completed = False
        if self.pk:
            previous = Milestone.objects.get(pk=self.pk)
            status_changed_to_completed = (
                previous.status != self.Status.COMPLETED and
                self.status == self.Status.COMPLETED
            )
        
        self.clean()
        super().save(*args, **kwargs)
        
        # Update phase progress if status changed to completed
        if status_changed_to_completed and self.phase:
            self.phase.update_progress()

    def complete(self):
        """Mark milestone as completed and set completion date"""
        self.status = self.Status.COMPLETED
        self.completion_date = timezone.now()
        self.completion_percentage = 100
        self.save()
    
    @property
    def logged_hours(self):
        """Calculate total hours logged for this milestone"""
        from django.db.models import Sum
        return self.time_entries.aggregate(total=Sum('hours'))['total'] or 0
        
    @property
    def hours_variance(self):
        """Calculate the variance between estimated and actual hours"""
        return self.estimated_hours - self.logged_hours
        
    @property
    def progress_based_on_time(self):
        """Calculate progress percentage based on logged time"""
        if not self.estimated_hours:
            return self.completion_percentage
            
        progress = min(100, int((self.logged_hours / self.estimated_hours) * 100))
        return progress
        
    def update_status_based_on_progress(self):
        """Update milestone status based on time entries progress"""
        if self.status == self.Status.COMPLETED:
            return
            
        if self.progress_based_on_time >= 100:
            self.status = self.Status.COMPLETED
            self.completion_date = timezone.now()
            self.completion_percentage = 100
            self.save()
        elif self.progress_based_on_time > 0:
            self.status = self.Status.IN_PROGRESS
            self.completion_percentage = self.progress_based_on_time
            self.save()

class ProjectDiscussion(BaseModel):
    """
    Represents a discussion thread within a project.
    Allows team members to collaborate and communicate.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='discussions'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('view_all_discussions', 'Can view all discussions'),
            ('manage_discussions', 'Can manage discussions'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.project.title}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validate title is not empty
        if not self.title.strip():
            raise ValidationError(_('Discussion title cannot be empty'))
    
    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        
        # Save the model first to ensure it has a pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Create notifications for team members when a new discussion is created
            self._create_notifications_for_team('created')
    
    def _create_notifications_for_team(self, notification_type):
        """
        Create notifications for all team members about this discussion.
        
        Args:
            notification_type (str): Type of notification (created, updated, etc.)
        """
        # Get all team members including the owner
        team_members = list(self.project.team_members.all())
        team_members.append(self.project.owner)
        
        # Create notifications for each member
        for member in team_members:
            # Skip notification for the user who created the discussion
            if notification_type == 'created' and member == self.created_by:
                continue
                
            # Skip notification for the user who updated the discussion
            if notification_type == 'updated' and member == self.updated_by:
                continue
            
            # Skip notification for the user who added the attachment
            if notification_type == 'attachment' and member == self.updated_by:
                continue
                
            # Determine notification creator
            notification_creator = None
            if notification_type == 'created':
                notification_creator = self.created_by
            elif notification_type in ['updated', 'attachment', 'comment', 'mention']:
                notification_creator = self.updated_by
            
            # Only create notification if we have a valid creator
            if notification_creator:
                DiscussionNotification.objects.create(
                    discussion=self,
                    user=member,
                    notification_type=notification_type,
                    created_by=notification_creator,
                    updated_by=notification_creator
                )

class DiscussionAttachment(BaseModel):
    """
    Represents a file attachment to a discussion.
    """
    discussion = models.ForeignKey(
        ProjectDiscussion,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='discussions/attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Attachment: {self.filename or self.file.name}"
    
    def save(self, *args, **kwargs):
        # Set filename if not provided
        if not self.filename and self.file:
            self.filename = self.file.name
            
        # Set file size
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
            
        # Set content type
        if self.file and not self.content_type:
            import mimetypes
            content_type, encoding = mimetypes.guess_type(self.file.name)
            if content_type:
                self.content_type = content_type
            else:
                self.content_type = 'application/octet-stream'
                
        super().save(*args, **kwargs)

class DiscussionNotification(BaseModel):
    """
    Represents a notification for a discussion action.
    """
    NOTIFICATION_TYPES = [
        ('created', 'Discussion Created'),
        ('updated', 'Discussion Updated'),
        ('comment', 'New Comment'),
        ('mention', 'User Mentioned'),
        ('attachment', 'New Attachment')
    ]
    
    discussion = models.ForeignKey(
        ProjectDiscussion,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='discussion_notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['discussion', 'notification_type']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.username} - {self.get_notification_type_display()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user"""
        cls.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now(),
            updated_at=timezone.now()
        )
