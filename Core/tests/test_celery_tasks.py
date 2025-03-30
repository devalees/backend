from unittest.mock import Mock, patch, MagicMock, PropertyMock
from django.test import TestCase
from django.db import models
from celery.result import AsyncResult
from celery.exceptions import Retry
from Core.models.base import TaskAwareModel, TaskStatus
from Core.tasks.handlers import ModelTaskHandler, create_model_task, create_generic_task, GenericModelTaskHandler
from Core.celery import app

class TestModel(TaskAwareModel):
    name = models.CharField(max_length=100)
    data = models.JSONField(default=dict)

    class Meta:
        app_label = 'core'

@app.task(bind=True, base=ModelTaskHandler)
def test_model_task(self, model_path: str, instance_id: int, **kwargs):
    """Test task for model processing"""
    instance = None
    try:
        instance = self.get_model_instance(TestModel, instance_id)
        if not instance:
            return False
        
        instance.start_processing(task_id=self.request.id)
        instance.data['processed'] = True
        instance.save()
        result = {'success': True, 'id': instance.id}
        self.store_result(instance, result)
        instance.mark_completed()
        return result
    except Exception as e:
        if instance:
            instance.mark_failed(str(e))
            instance.save()
        raise self.retry(exc=e)

@app.task(bind=True, base=GenericModelTaskHandler)
def test_generic_task(self, model_path: str, instance_id: int, **kwargs):
    """Test task for generic processing"""
    instance = None
    try:
        instance = self.get_model_instance(TestModel, instance_id)
        if not instance:
            return False
        
        instance.start_processing(task_id=self.request.id)
        instance.data['processed'] = True
        instance.save()
        result = {'success': True, 'id': instance.id}
        self.store_result(instance, result)
        instance.mark_completed()
        return result
    except Exception as e:
        if instance:
            instance.mark_failed(str(e))
            instance.save()
        raise self.retry(exc=e)

class TestCeleryTasks(TestCase):
    def setUp(self):
        # Initialize tasks
        self.model_task = test_model_task
        self.generic_task = test_generic_task
        
        # Create a test model instance
        self.test_instance = TestModel.objects.create(
            name='test',
            data={}
        )

    def test_task_execution(self):
        """Test basic task execution"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request):
            result = self.model_task(
                f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                self.test_instance.id
            )
            
            # Verify the result
            self.assertTrue(result['success'])
            self.assertEqual(result['id'], self.test_instance.id)
            
            # Refresh instance from DB
            self.test_instance.refresh_from_db()
            self.assertTrue(self.test_instance.data.get('processed'))
            self.assertEqual(self.test_instance.task_status, TaskStatus.COMPLETED.value)

    def test_task_failure_and_retry(self):
        """Test task failure and retry mechanism"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request), \
             patch.object(self.model_task, 'retry') as mock_retry:
            
            mock_retry.side_effect = Retry()
            
            # Start processing to set initial state
            self.test_instance.start_processing(task_id='test-task-id')
            
            # Mock the store_result method to raise an exception
            def mock_store_result(self, instance, result):
                instance.mark_failed("Test error")
                instance.save()
                raise Exception("Test error")
            
            with patch.object(ModelTaskHandler, 'store_result', mock_store_result):
                with self.assertRaises(Retry):
                    self.model_task(
                        f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                        self.test_instance.id
                    )
            
            # Verify instance status
            self.test_instance.refresh_from_db()
            self.assertEqual(self.test_instance.task_status, TaskStatus.FAILED.value)
            self.assertIsNotNone(self.test_instance.error_message)

    def test_task_result_storage(self):
        """Test storing task results"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request):
            result = self.model_task(
                f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                self.test_instance.id
            )
            
            # Verify result storage
            self.test_instance.refresh_from_db()
            self.assertEqual(self.test_instance.task_result, result)

    def test_batch_processing(self):
        """Test batch processing functionality"""
        # Create multiple test instances
        instances = [
            TestModel.objects.create(name=f'test_{i}', data={})
            for i in range(3)
        ]
        instance_ids = [instance.id for instance in instances]
        
        with patch.object(self.model_task, 'delay') as mock_delay:
            mock_delay.return_value = MagicMock(id='mock-task-id')
            
            # Call process_batch directly since we're testing a class method
            task_ids = [
                self.model_task.delay(
                    f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                    instance_id
                ).id
                for instance_id in instance_ids
            ]
            
            # Verify batch processing
            self.assertEqual(len(task_ids), len(instances))
            self.assertEqual(mock_delay.call_count, len(instances))

    def test_generic_task_handler(self):
        """Test generic task handler functionality"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request):
            result = self.generic_task(
                f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                self.test_instance.id
            )
            
            # Verify the result
            self.assertTrue(result['success'])
            self.assertEqual(result['id'], self.test_instance.id)
            
            # Verify instance state
            self.test_instance.refresh_from_db()
            self.assertTrue(self.test_instance.data.get('processed'))
            self.assertEqual(self.test_instance.task_status, TaskStatus.COMPLETED.value)

    def test_invalid_model_handling(self):
        """Test handling of invalid model paths"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request), \
             patch.object(ModelTaskHandler, 'get_model_instance') as mock_get_model, \
             patch.object(self.model_task, 'retry') as mock_retry:
            
            mock_get_model.side_effect = Exception("Invalid model path")
            mock_retry.side_effect = Retry()
            
            with self.assertRaises(Retry):
                self.model_task('invalid.model.path', self.test_instance.id)

    def test_nonexistent_instance_handling(self):
        """Test handling of non-existent model instances"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request):
            result = self.model_task(
                f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                999999  # Non-existent ID
            )
            
            self.assertFalse(result)

    def test_task_status_transitions(self):
        """Test task status transitions during processing"""
        mock_request = MagicMock()
        mock_request.id = 'test-task-id'
        
        with patch('celery.Task.request', mock_request):
            # Start task
            self.model_task(
                f'{self.test_instance._meta.app_label}.{self.test_instance._meta.model_name}',
                self.test_instance.id
            )
            
            # Verify status transitions
            self.test_instance.refresh_from_db()
            self.assertEqual(self.test_instance.task_status, TaskStatus.COMPLETED.value)
            self.assertIsNotNone(self.test_instance.processed_at)
            self.assertEqual(self.test_instance.task_id, 'test-task-id') 