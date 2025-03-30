from django.db import models
from Core.models.base import TaskAwareModel, TaskConfig

class ExampleModel(TaskAwareModel):
    name = models.CharField(max_length=255)
    data = models.JSONField(default=dict)
    
    # Optionally customize task configuration
    task_config = TaskConfig(
        status_field='task_status',
        error_field='error_message',
        processed_at_field='processed_at',
        task_id_field='task_id'
    )
    
    class Meta:
        verbose_name = 'Example'
        verbose_name_plural = 'Examples'
    
    def __str__(self):
        return f"{self.name} ({self.task_status})" 