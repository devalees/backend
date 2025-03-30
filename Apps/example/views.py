from rest_framework import viewsets
from Core.views.base import TaskAwareModelViewSet
from Core.tasks.handlers import create_generic_task, GenericModelTaskHandler
from .models import ExampleModel
from .serializers import ExampleModelSerializer

@create_generic_task('example.process_model')
class ProcessExampleTask(GenericModelTaskHandler):
    def __init__(self):
        super().__init__()
        self.set_process_callback(self.process_example)
        
    def process_example(self, instance, **kwargs):
        """Process an ExampleModel instance."""
        result = {
            'processed': True,
            'timestamp': instance.processed_at.isoformat() if instance.processed_at else None,
            'data': instance.data
        }
        
        # Update the instance
        instance.data['processed'] = True
        instance.save(update_fields=['data'])
        
        return result

class ExampleModelViewSet(TaskAwareModelViewSet):
    queryset = ExampleModel.objects.all()
    serializer_class = ExampleModelSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_task_handler(ProcessExampleTask()) 