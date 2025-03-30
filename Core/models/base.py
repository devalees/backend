from django.db import models
from django.utils import timezone
from typing import Optional, Dict, Any, ClassVar
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

@dataclass
class TaskConfig:
    status_field: str = 'task_status'
    error_field: str = 'error_message'
    processed_at_field: str = 'processed_at'
    task_id_field: str = 'task_id'
    result_field: str = 'task_result'

class TaskAwareModel(models.Model):
    """
    Base model class that includes task handling capabilities.
    All models that need task handling should inherit from this class.
    """
    task_status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in TaskStatus],
        default=TaskStatus.PENDING.value
    )
    task_id = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    task_result = models.JSONField(null=True, blank=True)

    # Task configuration that can be overridden by subclasses
    task_config: ClassVar[TaskConfig] = TaskConfig()

    class Meta:
        abstract = True

    def update_task_status(
        self,
        status: TaskStatus,
        error_message: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the task status and related fields.
        """
        try:
            setattr(self, self.task_config.status_field, status.value)
            update_fields = [self.task_config.status_field]

            if status == TaskStatus.COMPLETED:
                setattr(self, self.task_config.processed_at_field, timezone.now())
                update_fields.append(self.task_config.processed_at_field)

            if error_message is not None:
                setattr(self, self.task_config.error_field, error_message)
                update_fields.append(self.task_config.error_field)

            if extra_fields:
                for field, value in extra_fields.items():
                    setattr(self, field, value)
                    update_fields.append(field)

            self.save(update_fields=update_fields)
            return True
        except Exception as e:
            return False

    def start_processing(self, task_id: Optional[str] = None) -> bool:
        """Mark the model instance as being processed."""
        extra_fields = {}
        if task_id:
            extra_fields[self.task_config.task_id_field] = task_id
        return self.update_task_status(TaskStatus.PROCESSING, extra_fields=extra_fields)

    def mark_completed(self, **extra_fields) -> bool:
        """Mark the model instance as completed."""
        return self.update_task_status(TaskStatus.COMPLETED, extra_fields=extra_fields)

    def mark_failed(self, error_message: str, **extra_fields) -> bool:
        """Mark the model instance as failed."""
        return self.update_task_status(TaskStatus.FAILED, error_message=error_message, extra_fields=extra_fields)

    @property
    def is_processing(self) -> bool:
        """Check if the model instance is being processed."""
        return getattr(self, self.task_config.status_field) == TaskStatus.PROCESSING.value

    @property
    def is_completed(self) -> bool:
        """Check if the model instance has completed processing."""
        return getattr(self, self.task_config.status_field) == TaskStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Check if the model instance has failed processing."""
        return getattr(self, self.task_config.status_field) == TaskStatus.FAILED.value 