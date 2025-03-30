from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class TimeCategory(models.Model):
    """Categories for time entries (e.g., Development, Meeting, Break)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = "Time Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class TimeEntry(models.Model):
    """Individual time entries for tasks and projects"""
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

    class Meta:
        verbose_name_plural = "Time Entries"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.project.title} - {self.hours} hours"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time"))

class Timesheet(models.Model):
    """Weekly or monthly timesheet for users"""
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

    class Meta:
        ordering = ['-start_date']
        unique_together = ['user', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date}"

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))

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

class WorkSchedule(models.Model):
    """User's work schedule and availability"""
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
        if self.end_time <= self.start_time:
            raise ValidationError(_("End time must be after start time"))
