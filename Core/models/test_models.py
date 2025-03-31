from django.db import models
from .base import TaskAwareModel, TaskConfig

class TestTaskConfig(TaskConfig):
    """Test implementation of TaskConfig"""
    value = models.CharField(max_length=100, default='test')

    def __str__(self):
        return f"TestConfig: {self.value}"

class TestTaskAwareModel(TaskAwareModel):
    """Test implementation of TaskAwareModel"""
    name = models.CharField(max_length=100)
    task_config = models.OneToOneField(TestTaskConfig, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def mark_completed(self, **kwargs):
        """Mark the task as completed with optional extra fields."""
        self.complete_task()
        if kwargs:
            self.extra_fields = kwargs
            self.save()
        return True

    def mark_failed(self, error_message=None, **kwargs):
        """Mark the task as failed with an optional error message."""
        self.fail_task(error_message)
        if kwargs:
            self.extra_fields = kwargs
            self.save()
        return True

    def start_processing(self, task_id=None):
        """Start processing the task."""
        self.start_task(task_id)
        return True

    def update_task_status(self, status, **kwargs):
        """Update the task status with optional extra fields."""
        if status == 'completed':
            self.mark_completed(**kwargs)
        elif status == 'failed':
            self.mark_failed(**kwargs)
        elif status == 'cancelled':
            self.cancel_task()
        elif status == 'processing':
            self.start_processing()
        return True

    class Meta:
        app_label = 'Core'
        abstract = False 