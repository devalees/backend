from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from typing import Optional, Dict, Any, ClassVar
from dataclasses import dataclass
from enum import Enum
from .mixins import ImportExportMixin

User = get_user_model()

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

class BaseModelManager(models.Manager):
    """Manager for BaseModel that filters out inactive objects by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class BaseModel(ImportExportMixin, TaskAwareModel):
    """Base model with common fields, methods, and task handling capabilities"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_active = models.BooleanField(default=True)

    objects = BaseModelManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    # Import/Export configuration
    import_export_enabled = True  # Enable import/export by default for all models
    import_export_fields = None  # Use all non-relation fields by default

    def clean(self):
        """Base validation method"""
        super().clean()

    def save(self, *args, **kwargs):
        """Save the model with validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, hard=False, *args, **kwargs):
        """
        Soft delete the object by setting is_active to False.
        If hard is True, perform a hard delete.
        """
        if hard:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def hard_delete(self):
        """Hard delete the object"""
        models.Model.delete(self)

def get_current_user():
    """Get the current user from the thread local storage"""
    from threading import local
    _thread_locals = local()
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    """Set the current user in the thread local storage"""
    from threading import local
    _thread_locals = local()
    _thread_locals.user = user

@receiver(pre_save)
def set_user_fields(sender, instance, **kwargs):
    """Set created_by and updated_by fields before saving"""
    if not isinstance(instance, BaseModel):
        return

    user = get_current_user()
    if user and user.is_authenticated:
        if not instance.pk:  # New instance
            instance.created_by = user
        instance.updated_by = user 

class Config(BaseModel):
    """Model for storing system-wide configuration settings"""
    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True, null=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configurations'

    def __str__(self):
        return self.key

    def clean(self):
        """Validate configuration data"""
        # Check key length
        if len(self.key) > 255:
            raise ValidationError({"key": ["Configuration key cannot exceed 255 characters"]})

        # Check key uniqueness
        if Config.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError({"key": ["Configuration with this key already exists"]})

        # Check if non-editable config is being modified
        if not self.is_editable and self.pk:
            original = Config.objects.get(pk=self.pk)
            if original.value != self.value:
                raise ValidationError("This configuration setting cannot be modified")

    def save(self, *args, **kwargs):
        """Save the configuration and validate data"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of non-editable configurations"""
        if not self.is_editable:
            raise ValidationError("This configuration setting cannot be deleted")
        super().delete(*args, **kwargs) 