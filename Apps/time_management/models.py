from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from Apps.core.models import TaskAwareModel
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class TimeCategory(TaskAwareModel):
    """Categories for time entries (e.g., Development, Meeting, Break) with task handling capabilities"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    color = models.CharField(max_length=7, blank=True, default="#000000")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = "Time Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class TimeEntry(TaskAwareModel):
    """Individual time entries for tasks and projects with task handling capabilities"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    category = models.ForeignKey(TimeCategory, on_delete=models.PROTECT)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )
    is_billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_time_entries')
    
    # New fields for time management integration
    task = models.ForeignKey('project.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')
    project_phase = models.ForeignKey('project.ProjectPhase', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')
    milestone = models.ForeignKey('project.Milestone', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_entries')

    class Meta:
        verbose_name_plural = "Time Entries"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.project.title} - {self.hours} hours"

    def clean(self):
        super().clean()
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time"))
            
        # Ensure task belongs to the same project
        if self.task and self.task.project != self.project:
            raise ValidationError(_("Task must belong to the selected project"))
            
        # Ensure project_phase belongs to the project's schedule
        if self.project_phase and self.project_phase.schedule.project != self.project:
            raise ValidationError(_("Project phase must belong to the selected project's schedule"))
            
        # Ensure milestone belongs to the project's schedule
        if self.milestone and self.milestone.schedule.project != self.project:
            raise ValidationError(_("Milestone must belong to the selected project's schedule"))

    @property
    def get_related_task_status(self):
        """Return the status of the related task, if any"""
        return self.task.status if self.task else None
        
    @property
    def get_related_phase_name(self):
        """Return the name of the related project phase, if any"""
        return self.project_phase.name if self.project_phase else None
        
    @property
    def get_related_milestone_name(self):
        """Return the name of the related milestone, if any"""
        return self.milestone.name if self.milestone else None

class Timesheet(TaskAwareModel):
    """Weekly or monthly timesheet for users with task handling capabilities"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_timesheets')
    rejection_reason = models.TextField(blank=True, null=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rejected_timesheets')

    class Meta:
        ordering = ['-start_date']
        unique_together = ['user', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date}"

    def clean(self):
        super().clean()
        if self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
            
        # Ensure user doesn't have overlapping timesheets
        overlapping = Timesheet.objects.filter(
            user=self.user,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk if self.pk else -1)
        
        if overlapping.exists():
            raise ValidationError(_("Timesheet date range overlaps with an existing timesheet"))
    
    def save(self, *args, **kwargs):
        # Calculate total hours if not explicitly set
        if not self.total_hours and self.pk:
            self.calculate_total_hours()
            
        # Update timestamps based on status changes
        if self.pk:
            prev_state = Timesheet.objects.get(pk=self.pk)
            
            # If status changed to submitted
            if prev_state.status != 'submitted' and self.status == 'submitted':
                self.submitted_at = timezone.now()
                
            # If status changed to approved    
            elif prev_state.status != 'approved' and self.status == 'approved':
                self.approved_at = timezone.now()
                
            # If status changed to rejected
            elif prev_state.status != 'rejected' and self.status == 'rejected':
                self.rejected_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Calculate total hours after the initial save if it's a new object
        if not self.total_hours and not args and not kwargs.get('update_fields'):
            self.calculate_total_hours()
            if self.total_hours:
                # Save again with just the total_hours field to avoid infinite recursion
                Timesheet.objects.filter(pk=self.pk).update(total_hours=self.total_hours)
    
    def calculate_total_hours(self):
        """Calculate total hours from related timesheet entries"""
        from django.db.models import Sum
        
        total = self.entries.aggregate(sum=Sum('hours'))['sum'] or 0
        self.total_hours = total
        return total
    
    def submit(self):
        """Submit timesheet for approval"""
        if self.status != 'draft':
            raise ValidationError(_("Only draft timesheets can be submitted"))
            
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
        return True
    
    def approve(self, approver):
        """Approve the timesheet"""
        if self.status != 'submitted':
            raise ValidationError(_("Only submitted timesheets can be approved"))
            
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = approver
        self.save()
        return True
    
    def reject(self, rejecter, reason):
        """Reject the timesheet with a reason"""
        if self.status != 'submitted':
            raise ValidationError(_("Only submitted timesheets can be rejected"))
            
        self.status = 'rejected'
        self.rejected_at = timezone.now()
        self.rejected_by = rejecter
        self.rejection_reason = reason
        self.save()
        return True
    
    def return_to_draft(self):
        """Return a submitted or rejected timesheet to draft status"""
        if self.status not in ['submitted', 'rejected']:
            raise ValidationError(_("Only submitted or rejected timesheets can be returned to draft"))
            
        self.status = 'draft'
        self.submitted_at = None
        self.save()
        return True
    
    def get_time_entries_for_period(self):
        """Get all time entries for this timesheet period"""
        return TimeEntry.objects.filter(
            user=self.user,
            start_time__date__gte=self.start_date,
            end_time__date__lte=self.end_date
        )
    
    def add_time_entries(self):
        """Add missing time entries for this timesheet period to the timesheet"""
        entries = self.get_time_entries_for_period()
        added_count = 0
        
        for entry in entries:
            # Skip if already in timesheet
            if TimesheetEntry.objects.filter(timesheet=self, time_entry=entry).exists():
                continue
                
            # Add to timesheet
            TimesheetEntry.objects.create(
                timesheet=self,
                time_entry=entry,
                date=entry.start_time.date(),
                category=entry.category,
                description=entry.description,
                hours=entry.hours
            )
            added_count += 1
            
        # Update total hours
        self.calculate_total_hours()
        self.save()
        
        return added_count
    
    def get_approval_history(self):
        """Get approval workflow history"""
        history = []
        
        if self.created_at:
            history.append({
                'action': 'created',
                'timestamp': self.created_at,
                'user': self.created_by
            })
            
        if self.submitted_at:
            history.append({
                'action': 'submitted',
                'timestamp': self.submitted_at,
                'user': self.user
            })
            
        if self.approved_at:
            history.append({
                'action': 'approved',
                'timestamp': self.approved_at,
                'user': self.approved_by
            })
            
        if self.rejected_at:
            history.append({
                'action': 'rejected',
                'timestamp': self.rejected_at,
                'user': self.rejected_by,
                'reason': self.rejection_reason
            })
            
        # Sort by timestamp
        return sorted(history, key=lambda x: x['timestamp'])

class TimesheetEntry(models.Model):
    """Individual entries within a timesheet"""
    timesheet = models.ForeignKey(Timesheet, on_delete=models.CASCADE, related_name='entries')
    time_entry = models.ForeignKey(TimeEntry, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(TimeCategory, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True)
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = "Timesheet Entries"
        unique_together = ['timesheet', 'time_entry']
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.timesheet.user.username} - {self.date} ({self.hours} hours)"

class WorkSchedule(TaskAwareModel):
    """User's work schedule and availability with task handling capabilities"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="Default Schedule")
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.JSONField()  # List of days (0-6, where 0 is Monday)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', 'start_time']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def clean(self):
        super().clean()
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time"))
            
        # Validate days_of_week format
        if not isinstance(self.days_of_week, list):
            raise ValidationError(_("Days of week must be a list"))
            
        for day in self.days_of_week:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValidationError(_("Days of week must contain integers between 0 and 6"))
    
    @property
    def daily_capacity_hours(self):
        """Calculate daily capacity in hours"""
        hours = self.end_time.hour - self.start_time.hour
        minutes = self.end_time.minute - self.start_time.minute
        
        return hours + (minutes / 60)
    
    @property
    def weekly_capacity_hours(self):
        """Calculate weekly capacity in hours"""
        return self.daily_capacity_hours * len(self.days_of_week)
    
    @property
    def monthly_capacity_hours(self):
        """Calculate monthly capacity (approx 4 weeks) in hours"""
        return self.weekly_capacity_hours * 4
    
    def get_capacity_for_date_range(self, start_date, end_date):
        """
        Calculate capacity in hours for a specific date range
        
        Args:
            start_date: Beginning date (inclusive)
            end_date: Ending date (inclusive)
            
        Returns:
            Total available hours for the date range
        """
        if start_date > end_date:
            return 0
            
        # Count working days in the range
        current_date = start_date
        working_days = 0
        
        while current_date <= end_date:
            # Get day of week (0 = Monday, 6 = Sunday)
            weekday = current_date.weekday()
            if weekday in self.days_of_week:
                working_days += 1
            current_date += timezone.timedelta(days=1)
            
        return working_days * self.daily_capacity_hours
    
    def get_utilized_capacity(self, start_date, end_date):
        """
        Calculate utilized capacity based on time entries in a date range
        
        Args:
            start_date: Beginning date 
            end_date: Ending date
            
        Returns:
            Dictionary with capacity statistics
        """
        from django.db.models import Sum
        
        # Get capacity for date range
        total_capacity = self.get_capacity_for_date_range(start_date, end_date)
        
        # Get time entries for the user in this date range
        logged_hours = TimeEntry.objects.filter(
            user=self.user,
            start_time__date__gte=start_date,
            end_time__date__lte=end_date
        ).aggregate(total=Sum('hours'))['total'] or 0
        
        # Calculate utilization
        utilization_percentage = (logged_hours / total_capacity * 100) if total_capacity > 0 else 0
        available_hours = max(0, total_capacity - logged_hours)
        
        return {
            'total_capacity_hours': total_capacity,
            'logged_hours': logged_hours,
            'utilization_percentage': utilization_percentage,
            'available_hours': available_hours
        }
    
    @classmethod
    def get_team_capacity(cls, users, start_date, end_date):
        """
        Calculate team capacity for a group of users
        
        Args:
            users: List of user ids or User queryset
            start_date: Beginning date
            end_date: Ending date
            
        Returns:
            Dictionary with team capacity statistics
        """
        total_capacity = 0
        total_logged = 0
        user_capacities = []
        
        # Get active schedules for users
        schedules = cls.objects.filter(user__in=users, is_active=True)
        
        for schedule in schedules:
            utilization = schedule.get_utilized_capacity(start_date, end_date)
            total_capacity += utilization['total_capacity_hours']
            total_logged += utilization['logged_hours']
            
            user_capacities.append({
                'user_id': schedule.user.id,
                'username': schedule.user.username,
                'capacity_hours': utilization['total_capacity_hours'],
                'logged_hours': utilization['logged_hours'],
                'utilization_percentage': utilization['utilization_percentage'],
                'available_hours': utilization['available_hours']
            })
        
        # Calculate team utilization
        team_utilization = (total_logged / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            'team_capacity_hours': total_capacity,
            'team_logged_hours': total_logged,
            'team_utilization_percentage': team_utilization,
            'team_available_hours': max(0, total_capacity - total_logged),
            'user_capacities': user_capacities
        }
