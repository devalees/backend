from django.test import TestCase
from celery import Celery
from unittest.mock import patch, MagicMock
from celery import shared_task
from Core.models.test_models import TestTaskAwareModel, TestTaskConfig

class TestTaskRouting(TestCase):
    def setUp(self):
        # Create a test Celery app
        self.app = Celery('test')
        
        # Configure task routing
        self.app.conf.update(
            task_routes={
                'high_priority_task': {'queue': 'high_priority'},
                'low_priority_task': {'queue': 'low_priority'},
                'default_task': {'queue': 'default'}
            }
        )

        self.task_config = TestTaskConfig.objects.create(
            max_retries=3,
            retry_delay=60,
            timeout=300,
            priority='high',
            queue='high_priority'
        )
        self.model = TestTaskAwareModel.objects.create(
            name='test_model',
            task_config=self.task_config
        )

        # Define test tasks
        @self.app.task(name='high_priority_task')
        def high_priority_task():
            return 1
        self.high_priority_task = high_priority_task

        @self.app.task(name='low_priority_task')
        def low_priority_task():
            return 1
        self.low_priority_task = low_priority_task

        @self.app.task(name='default_task')
        def default_task():
            return 1
        self.default_task = default_task

        @self.app.task(name='test_task_with_retry')
        def test_task_with_retry():
            return 1
        self.test_task_with_retry = test_task_with_retry

    def test_high_priority_routing(self):
        with patch.object(self.high_priority_task, 'apply_async') as mock_apply:
            self.high_priority_task.apply_async()
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'high_priority')

    def test_low_priority_routing(self):
        with patch.object(self.low_priority_task, 'apply_async') as mock_apply:
            self.low_priority_task.apply_async()
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'low_priority')

    def test_default_routing(self):
        with patch.object(self.default_task, 'apply_async') as mock_apply:
            self.default_task.apply_async()
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'default')

    def test_custom_routing_options(self):
        with patch.object(self.default_task, 'apply_async') as mock_apply:
            self.default_task.apply_async(queue='custom_queue')
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'custom_queue')

    def test_task_routing_with_retry(self):
        with patch.object(self.test_task_with_retry, 'apply_async') as mock_apply:
            self.test_task_with_retry.apply_async(
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

    def test_task_with_retry(self):
        with patch.object(self.test_task_with_retry, 'apply_async') as mock_apply:
            self.test_task_with_retry.apply_async(
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