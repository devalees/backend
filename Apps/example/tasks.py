from Core.tasks.handlers import ModelTaskHandler, create_model_task
from .models import ExampleModel
from typing import Dict, Any

@create_model_task('example.process_model')
class ProcessExampleTask(ModelTaskHandler):
    def process_instance(self, instance: ExampleModel, **kwargs) -> Dict[str, Any]:
        """
        Process an ExampleModel instance.
        The task status handling is automatically managed by ModelTaskHandler.
        
        Args:
            instance: The ExampleModel instance to process
            **kwargs: Additional arguments passed to the task
            
        Returns:
            Dict containing processing results
        """
        # Your processing logic here
        result = {
            'processed': True,
            'timestamp': instance.processed_at.isoformat() if instance.processed_at else None,
            'data': instance.data
        }
        
        # Update the instance
        instance.data['processed'] = True
        instance.save(update_fields=['data'])
        
        return result

# Usage examples:
# 1. Process a single instance
# ProcessExampleTask.delay('Apps.example.models.ExampleModel', instance_id=1)
#
# 2. Process multiple instances in parallel
# task_ids = ProcessExampleTask.process_batch(
#     'Apps.example.models.ExampleModel',
#     instance_ids=[1, 2, 3]
# )
#
# 3. Process with additional arguments
# ProcessExampleTask.delay(
#     'Apps.example.models.ExampleModel',
#     instance_id=1,
#     extra_param='value'
# ) 