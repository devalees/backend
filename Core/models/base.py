from django.db import models
from enum import Enum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class TaskStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class TaskConfig(models.Model):
    """Base configuration for task-aware models"""
    max_retries = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=60)
    timeout = models.IntegerField(default=300)
    priority = models.IntegerField(default=0)
    queue = models.CharField(max_length=50, default='default')

    class Meta:
        abstract = True

class TaskAwareModel(models.Model):
    """Base model for task-aware models"""
    task_id = models.CharField(max_length=100, null=True, blank=True)
    task_status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name.title()) for status in TaskStatus],
        default=TaskStatus.PENDING.value
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    extra_fields = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def start_task(self, task_id=None):
        """Start the task with an optional task ID."""
        self.task_id = task_id
        self.task_status = TaskStatus.PROCESSING.value
        self.started_at = timezone.now()
        self.processed_at = timezone.now()
        self.save()

    def complete_task(self, **kwargs):
        """Complete the task with optional extra fields."""
        self.task_status = TaskStatus.COMPLETED.value
        self.completed_at = timezone.now()
        if kwargs:
            self.extra_fields = kwargs
        self.save()

    def fail_task(self, error_message=None):
        """Fail the task with an optional error message."""
        self.task_status = TaskStatus.FAILED.value
        self.completed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save()

    def cancel_task(self):
        """Cancel the task."""
        self.task_status = TaskStatus.CANCELLED.value
        self.completed_at = timezone.now()
        self.save()

    def clean(self):
        """Validate the model."""
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValidationError("Completion time cannot be earlier than start time")

    def save(self, *args, **kwargs):
        """Save the model after validation."""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_pending(self):
        """Check if the task is pending."""
        return self.task_status == TaskStatus.PENDING.value

    @property
    def is_processing(self):
        """Check if the task is processing."""
        return self.task_status == TaskStatus.PROCESSING.value

    @property
    def is_completed(self):
        """Check if the task is completed."""
        return self.task_status == TaskStatus.COMPLETED.value

    @property
    def is_failed(self):
        """Check if the task is failed."""
        return self.task_status == TaskStatus.FAILED.value

    @property
    def is_cancelled(self):
        """Check if the task is cancelled."""
        return self.task_status == TaskStatus.CANCELLED.value

    def get_task_duration(self):
        """Calculate the duration of the task."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def get_task_status_display(self):
        """Get the human-readable status of the task."""
        return dict(self._meta.get_field('task_status').choices)[self.task_status]

    def mark_completed(self, **kwargs):
        self.complete_task()
        if kwargs:
            self.extra_fields = kwargs
            self.save()
        return True

    def mark_failed(self, error_message=None, **kwargs):
        self.fail_task(error_message)
        if kwargs:
            self.extra_fields = kwargs
            self.save()
        return True

    def start_processing(self):
        self.start_task()
        return True

    def update_task_status(self, status, **kwargs):
        if status == 'completed':
            self.mark_completed(**kwargs)
        elif status == 'failed':
            self.mark_failed(**kwargs)
        elif status == 'cancelled':
            self.cancel_task()
        elif status == 'processing':
            self.start_processing()
        return True 