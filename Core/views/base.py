from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.apps import apps
from Core.tasks.handlers import GenericModelTaskHandler
from Core.models.base import TaskAwareModel

class TaskAwareModelViewSet(viewsets.ModelViewSet):
    """
    A generic viewset for TaskAwareModel that provides task processing capabilities.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_handler = None

    def set_task_handler(self, task_handler: GenericModelTaskHandler):
        """Set the task handler for this viewset."""
        self.task_handler = task_handler

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Process a single instance using the task system.
        """
        if not self.task_handler:
            return Response(
                {'error': 'No task handler configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        instance = self.get_object()
        task = self.task_handler.delay(
            f'{instance._meta.app_label}.{instance._meta.model_name}',
            instance_id=instance.id,
            **request.data
        )
        return Response({
            'task_id': task.id,
            'status': 'Task started',
            'instance_id': instance.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def process_batch(self, request):
        """
        Process multiple instances in parallel.
        """
        if not self.task_handler:
            return Response(
                {'error': 'No task handler configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        instance_ids = request.data.get('instance_ids', [])
        if not instance_ids:
            return Response(
                {'error': 'No instance IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task_ids = self.task_handler.process_batch(
            f'{self.queryset.model._meta.app_label}.{self.queryset.model._meta.model_name}',
            instance_ids=instance_ids,
            **request.data.get('kwargs', {})
        )
        
        return Response({
            'task_ids': task_ids,
            'status': f'Started processing {len(task_ids)} instances'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def task_status(self, request, pk=None):
        """
        Get the current task status for an instance.
        """
        instance = self.get_object()
        return Response({
            'instance_id': instance.id,
            'task_status': instance.task_status,
            'task_id': instance.task_id,
            'error_message': instance.error_message,
            'processed_at': instance.processed_at,
            'task_result': instance.task_result
        }) 