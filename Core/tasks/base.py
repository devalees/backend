from celery import Task
from typing import Any, Dict, Optional
from django.db import models
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

class BaseTaskWithRetry(Task):
    """Base task class with retry mechanism and logging."""
    
    max_retries = 3
    default_retry_delay = 60  # 1 minute
    
    def apply_async(self, *args, **kwargs):
        """Override to add custom logic before task execution"""
        return super().apply_async(*args, **kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure with logging"""
        logger.error(
            f"Task {task_id} failed: {exc}\nArgs: {args}\nKwargs: {kwargs}",
            exc_info=einfo,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success with logging"""
        logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)

class ModelTaskMixin:
    """Mixin for tasks that operate on Django models."""
    
    @classmethod
    def get_model_instance(cls, model_class: models.Model, instance_id: int) -> Optional[models.Model]:
        """Safely get model instance with logging."""
        try:
            return model_class.objects.get(id=instance_id)
        except model_class.DoesNotExist:
            logger.error(f"{model_class.__name__} with id {instance_id} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error fetching {model_class.__name__} with id {instance_id}: {str(e)}")
            return None

    @classmethod
    def update_model_status(
        cls,
        instance: models.Model,
        status_field: str,
        new_status: str,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update model status and additional fields safely.
        Returns True if update was successful, False otherwise.
        """
        try:
            update_fields = [status_field]
            setattr(instance, status_field, new_status)
            
            if extra_fields:
                for field, value in extra_fields.items():
                    setattr(instance, field, value)
                    update_fields.append(field)
            
            instance.save(update_fields=update_fields)
            return True
        except Exception as e:
            logger.error(f"Error updating {instance.__class__.__name__} status: {str(e)}")
            return False 