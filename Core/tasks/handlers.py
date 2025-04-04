from typing import Type, Optional, Any, Dict, List
from celery import Task
from django.db import models
from celery.utils.log import get_task_logger
from Core.celery import app
from Core.models.base import TaskAwareModel
from django.utils import timezone

logger = get_task_logger(__name__)

class ModelTaskHandler(Task):
    """
    A generic task handler for processing TaskAwareModel instances.
    This handler automatically manages task status and provides error handling.
    """
    
    abstract = True
    max_retries = 3
    default_retry_delay = 60  # 1 minute
    
    def get_model_instance(
        self,
        model_class: Type[TaskAwareModel],
        instance_id: int
    ) -> Optional[TaskAwareModel]:
        """Safely get model instance with logging."""
        try:
            return model_class.objects.get(id=instance_id)
        except model_class.DoesNotExist:
            logger.error(f"{model_class.__name__} with id {instance_id} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error fetching {model_class.__name__} with id {instance_id}: {str(e)}")
            return None

    def check_dependencies(self, instance: TaskAwareModel) -> bool:
        """
        Check if all dependencies are satisfied for the given task instance.
        Returns True if all dependencies are completed, False otherwise.
        """
        try:
            # Check if the instance has dependencies
            if not hasattr(instance, 'dependencies'):
                return True

            # Get all incomplete dependencies
            incomplete_deps = instance.dependencies.filter(
                dependency_task__task_status__in=['pending', 'processing', 'failed']
            )

            if incomplete_deps.exists():
                logger.info(
                    f"Task {instance.id} has incomplete dependencies: "
                    f"{list(incomplete_deps.values_list('dependency_task_id', flat=True))}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking dependencies for task {instance.id}: {str(e)}")
            return False

    def process_instance(
        self,
        instance: TaskAwareModel,
        **kwargs
    ) -> Any:
        """
        Override this method in your task to implement the actual processing logic.
        """
        raise NotImplementedError("Subclasses must implement process_instance()")

    def store_result(self, instance: TaskAwareModel, result: Any) -> bool:
        """
        Store the task result in the model instance.
        """
        try:
            setattr(instance, instance.task_config.result_field, result)
            instance.save(update_fields=[instance.task_config.result_field])
            return True
        except Exception as e:
            logger.error(f"Error storing result for {instance.__class__.__name__} {instance.id}: {str(e)}")
            return False

    def run(self, model_path: str, instance_id: int, **kwargs):
        """
        Main task execution method.
        
        Args:
            model_path: Full path to the model class (e.g., 'myapp.models.MyModel')
            instance_id: ID of the model instance to process
            **kwargs: Additional arguments to pass to process_instance
        """
        try:
            # Import the model class dynamically
            module_path, class_name = model_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            model_class = getattr(module, class_name)
            
            if not issubclass(model_class, TaskAwareModel):
                raise ValueError(f"{model_path} is not a subclass of TaskAwareModel")
            
            # Get the instance
            instance = self.get_model_instance(model_class, instance_id)
            if not instance:
                return False
            
            # Check dependencies
            if not self.check_dependencies(instance):
                logger.info(f"Task {instance_id} dependencies not satisfied, retrying in {self.default_retry_delay}s")
                raise self.retry(countdown=self.default_retry_delay)
            
            # Start processing
            instance.start_processing(task_id=self.request.id)
            
            # Process the instance
            result = self.process_instance(instance, **kwargs)
            
            # Store the result
            self.store_result(instance, result)
            
            # Mark as completed
            instance.mark_completed()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {model_path} instance {instance_id}: {str(e)}")
            if 'instance' in locals():
                instance.mark_failed(str(e))
            raise self.retry(exc=e)

    @classmethod
    def process_batch(
        cls,
        model_path: str,
        instance_ids: list[int],
        **kwargs
    ) -> list[str]:
        """
        Process multiple instances in parallel.
        
        Args:
            model_path: Full path to the model class
            instance_ids: List of instance IDs to process
            **kwargs: Additional arguments to pass to each task
            
        Returns:
            List of task IDs
        """
        task_ids = []
        for instance_id in instance_ids:
            task = cls.delay(model_path, instance_id, **kwargs)
            task_ids.append(task.id)
        return task_ids

def create_model_task(name: str, **task_options):
    """
    Decorator factory to create model-specific tasks.
    
    Usage:
    @create_model_task('my_app.process_model')
    class ProcessModelTask(ModelTaskHandler):
        def process_instance(self, instance, **kwargs):
            # Implementation here
            pass
    """
    def decorator(task_class):
        if not issubclass(task_class, ModelTaskHandler):
            raise TypeError("Task class must inherit from ModelTaskHandler")
        return app.task(name=name, base=task_class, bind=True, **task_options)
    return decorator

class GenericModelTaskHandler(ModelTaskHandler):
    """
    A generic task handler that can process any TaskAwareModel instance.
    This handler allows for dynamic processing logic through callbacks.
    """
    
    def __init__(self):
        super().__init__()
        self._process_callback = None
        self._pre_process_callback = None
        self._post_process_callback = None

    def set_process_callback(self, callback):
        """Set the main processing callback function."""
        self._process_callback = callback

    def set_pre_process_callback(self, callback):
        """Set the pre-processing callback function."""
        self._pre_process_callback = callback

    def set_post_process_callback(self, callback):
        """Set the post-processing callback function."""
        self._post_process_callback = callback

    def process_instance(
        self,
        instance: TaskAwareModel,
        **kwargs
    ) -> Any:
        """
        Process an instance using the registered callbacks.
        """
        if not self._process_callback:
            raise NotImplementedError("No process callback registered")

        # Pre-process hook
        if self._pre_process_callback:
            self._pre_process_callback(instance, **kwargs)

        # Main processing
        result = self._process_callback(instance, **kwargs)

        # Post-process hook
        if self._post_process_callback:
            self._post_process_callback(instance, result, **kwargs)

        return result

def create_generic_task(name: str, **task_options):
    """
    Decorator factory to create generic model tasks.
    
    Usage:
    @create_generic_task('my_app.process_model')
    class ProcessModelTask(GenericModelTaskHandler):
        def __init__(self):
            super().__init__()
            self.set_process_callback(self.my_process_function)
            
        def my_process_function(self, instance, **kwargs):
            # Implementation here
            pass
    """
    def decorator(task_class):
        if not issubclass(task_class, GenericModelTaskHandler):
            raise TypeError("Task class must inherit from GenericModelTaskHandler")
        return app.task(name=name, base=task_class, bind=True, **task_options)
    return decorator 