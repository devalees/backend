from django.test import TestCase
from Core.celery import app
from celery.result import AsyncResult
from unittest.mock import patch

class CeleryTasksTest(TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = app

    def test_celery_app_config(self):
        """Test Celery app configuration"""
        self.assertIsNotNone(self.app.conf)
        self.assertEqual(self.app.conf.task_serializer, 'json')
        self.assertEqual(self.app.conf.result_serializer, 'json')
        self.assertEqual(self.app.conf.accept_content, ['json'])
        self.assertEqual(self.app.conf.result_expires, 3600)
        self.assertEqual(self.app.conf.task_always_eager, False)

    def test_celery_task_execution(self):
        """Test basic Celery task execution"""
        with patch('celery.app.task.Task.apply_async') as mock_apply:
            mock_apply.return_value = AsyncResult('test-task-id')
            
            # Test task execution
            result = self.app.send_task('test_task')
            self.assertIsNotNone(result)
            self.assertEqual(result.id, 'test-task-id')
            mock_apply.assert_called_once()

    def test_celery_task_retry(self):
        """Test Celery task retry mechanism"""
        with patch('celery.app.task.Task.apply_async') as mock_apply:
            mock_apply.side_effect = Exception('Test error')
            
            # Test retry behavior
            with self.assertRaises(Exception):
                self.app.send_task('test_task')
            
            # Verify retry was attempted
            self.assertEqual(mock_apply.call_count, 3)

    def test_celery_task_error_handling(self):
        """Test Celery task error handling"""
        with patch('celery.app.task.Task.apply_async') as mock_apply:
            mock_apply.side_effect = Exception('Test error')
            
            # Test error handling
            with self.assertRaises(Exception) as context:
                self.app.send_task('test_task')
            
            self.assertEqual(str(context.exception), 'Test error')

    def test_celery_task_result_storage(self):
        """Test Celery task result storage"""
        with patch('celery.app.task.Task.apply_async') as mock_apply:
            mock_apply.return_value = AsyncResult('test-task-id')
            
            # Test result storage
            result = self.app.send_task('test_task')
            self.assertIsNotNone(result.id)
            self.assertIsNotNone(result.status) 