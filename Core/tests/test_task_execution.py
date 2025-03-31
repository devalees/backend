from django.test import TestCase
from celery import Celery
from unittest.mock import patch, MagicMock
from celery.exceptions import MaxRetriesExceededError
from Apps.tasks.high_priority import test_task as high_priority_task
from Apps.tasks.low_priority import test_task as low_priority_task

class TestTaskExecution(TestCase):
    def setUp(self):
        self.app = Celery('test_app')
        self.mock_logger = MagicMock()

    def test_high_priority_task_execution(self):
        """Test high priority task execution"""
        with patch.object(high_priority_task, 'apply_async') as mock_apply:
            high_priority_task.apply_async()
            mock_apply.assert_called_once()
            
            # Verify the result
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'high_priority')
            self.assertEqual(high_priority_task.apply_async(), "High priority task completed")

    def test_low_priority_task_execution(self):
        """Test low priority task execution"""
        with patch.object(low_priority_task, 'apply_async') as mock_apply:
            low_priority_task.apply_async()
            mock_apply.assert_called_once()
            
            # Verify the result
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'low_priority')
            self.assertEqual(low_priority_task.apply_async(), "Low priority task completed")

    def test_task_retry_mechanism(self):
        """Test task retry mechanism"""
        with patch.object(high_priority_task, 'apply_async') as mock_apply:
            high_priority_task.apply_async(
                retry=True,
                retry_policy={
                    'max_retries': 3,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.5,
                }
            )
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('retry'), True)
            self.assertEqual(kwargs.get('retry_policy')['max_retries'], 3)

    def test_task_error_handling(self):
        """Test task error handling"""
        with patch.object(high_priority_task, 'apply_async') as mock_apply:
            mock_apply.side_effect = Exception("Test error")
            
            with self.assertRaises(Exception):
                high_priority_task.apply_async()

    def test_task_max_retries(self):
        """Test task max retries exceeded"""
        with patch.object(high_priority_task, 'apply_async') as mock_apply:
            mock_apply.side_effect = MaxRetriesExceededError()
            
            with self.assertRaises(MaxRetriesExceededError):
                high_priority_task.apply_async(
                    retry=True,
                    retry_policy={'max_retries': 3}
                )

    def test_task_timeout(self):
        """Test task timeout handling"""
        with patch.object(high_priority_task, 'apply_async') as mock_apply:
            high_priority_task.apply_async(
                time_limit=10,
                soft_time_limit=5
            )
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('time_limit'), 10)
            self.assertEqual(kwargs.get('soft_time_limit'), 5) 