from django.test import TestCase
from celery import Celery, signals
from unittest.mock import patch, MagicMock
from Core.models.test_models import TestTaskAwareModel, TestTaskConfig

class TestTaskMonitoring(TestCase):
    def setUp(self):
        self.app = Celery('test_app')
        self.mock_logger = MagicMock()
        self.task_config = TestTaskConfig.objects.create(
            max_retries=3,
            retry_delay=60,
            timeout=300,
            priority=5,
            queue='default'
        )
        self.model = TestTaskAwareModel.objects.create(
            name='Test Model',
            task_config=self.task_config
        )

        # Define signal handlers
        @signals.task_sent.connect
        def task_sent_handler(sender=None, task_id=None, task=None, **kwargs):
            self.mock_logger.info(f"Task sent: {task_id}")

        @signals.task_received.connect
        def task_received_handler(sender=None, request=None, **kwargs):
            self.mock_logger.info(f"Task received: {request.id}")

        @signals.task_success.connect
        def task_success_handler(sender=None, result=None, **kwargs):
            self.mock_logger.info(f"Task succeeded: {sender.request.id}")

        @signals.task_failure.connect
        def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
            self.mock_logger.info(f"Task failed: {task_id}, error: {str(exception)}")

        self.handlers = [
            task_sent_handler,
            task_received_handler,
            task_success_handler,
            task_failure_handler
        ]

    def tearDown(self):
        # Disconnect all signal handlers
        signals.task_sent.disconnect(self.handlers[0])
        signals.task_received.disconnect(self.handlers[1])
        signals.task_success.disconnect(self.handlers[2])
        signals.task_failure.disconnect(self.handlers[3])

    def test_task_sent_signal(self):
        task_id = 'test-task-123'
        self.model.start_task(task_id)
        self.mock_logger.info.assert_called_with(f"Task sent: {task_id}")

    def test_task_received_signal(self):
        task_id = 'test-task-123'
        request = MagicMock()
        request.id = task_id
        signals.task_received.send(sender=None, request=request)
        self.mock_logger.info.assert_called_with(f"Task received: {task_id}")

    def test_task_success_signal(self):
        task_id = 'test-task-123'
        sender = MagicMock()
        sender.request.id = task_id
        signals.task_success.send(sender=sender, result=None)
        self.mock_logger.info.assert_called_with(f"Task succeeded: {task_id}")

    def test_task_failure_signal(self):
        task_id = 'test-task-123'
        exception = Exception("Test error")
        signals.task_failure.send(sender=None, task_id=task_id, exception=exception)
        self.mock_logger.info.assert_called_with(f"Task failed: {task_id}, error: Test error")

    def test_task_monitoring_integration(self):
        task_id = 'test-task-123'
        
        # Test task sent
        self.model.start_task(task_id)
        self.mock_logger.info.assert_called_with(f"Task sent: {task_id}")
        self.mock_logger.info.reset_mock()

        # Test task received
        request = MagicMock()
        request.id = task_id
        signals.task_received.send(sender=None, request=request)
        self.mock_logger.info.assert_called_with(f"Task received: {task_id}")
        self.mock_logger.info.reset_mock()

        # Test task success
        sender = MagicMock()
        sender.request.id = task_id
        signals.task_success.send(sender=sender, result=None)
        self.mock_logger.info.assert_called_with(f"Task succeeded: {task_id}")
        self.mock_logger.info.reset_mock()

        # Test task failure
        exception = Exception("Test error")
        signals.task_failure.send(sender=None, task_id=task_id, exception=exception)
        self.mock_logger.info.assert_called_with(f"Task failed: {task_id}, error: Test error") 