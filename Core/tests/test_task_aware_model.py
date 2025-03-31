import pytest
from django.test import TestCase
from django.utils import timezone
from Core.models.base import TaskAwareModel, TaskStatus
from Core.models.test_models import TestTaskAwareModel, TestTaskConfig
from django.db import models
from datetime import timedelta

class TestTaskAwareModelTests(TestCase):
    def setUp(self):
        self.task_config = TestTaskConfig.objects.create(
            max_retries=3,
            retry_delay=60,
            timeout=300,
            priority=1,
            queue='default'
        )
        self.model = TestTaskAwareModel.objects.create(
            name='test_task',
            task_config=self.task_config
        )

    def test_initial_state(self):
        self.assertEqual(self.model.task_status, TaskStatus.PENDING)
        self.assertIsNone(self.model.task_id)
        self.assertIsNone(self.model.error_message)
        self.assertIsNone(self.model.completed_at)
        self.assertIsNone(self.model.processed_at)

    def test_start_task(self):
        self.model.start_task()
        self.assertEqual(self.model.task_status, TaskStatus.PROCESSING)
        self.assertIsNotNone(self.model.processed_at)

    def test_complete_task(self):
        self.model.complete_task()
        self.assertEqual(self.model.task_status, TaskStatus.COMPLETED)
        self.assertIsNotNone(self.model.completed_at)

    def test_fail_task(self):
        error_message = "Task failed"
        self.model.fail_task(error_message)
        self.assertEqual(self.model.task_status, TaskStatus.FAILED)
        self.assertEqual(self.model.error_message, error_message)

    def test_cancel_task(self):
        self.model.cancel_task()
        self.assertEqual(self.model.task_status, TaskStatus.CANCELLED)

    def test_task_status_checks(self):
        self.assertTrue(self.model.is_pending)
        self.assertFalse(self.model.is_processing)
        self.assertFalse(self.model.is_completed)
        self.assertFalse(self.model.is_failed)
        self.assertFalse(self.model.is_cancelled)

        self.model.start_task()
        self.assertFalse(self.model.is_pending)
        self.assertTrue(self.model.is_processing)
        self.assertFalse(self.model.is_completed)
        self.assertFalse(self.model.is_failed)
        self.assertFalse(self.model.is_cancelled)

        self.model.complete_task()
        self.assertFalse(self.model.is_pending)
        self.assertFalse(self.model.is_processing)
        self.assertTrue(self.model.is_completed)
        self.assertFalse(self.model.is_failed)
        self.assertFalse(self.model.is_cancelled)

    def test_mark_completed(self):
        extra_fields = {'result': 'success'}
        self.model.mark_completed(extra_fields)
        self.assertEqual(self.model.task_status, TaskStatus.COMPLETED)
        self.assertEqual(self.model.extra_fields, extra_fields)

    def test_mark_failed(self):
        error_message = "Task failed"
        extra_fields = {'error_code': 500}
        self.model.mark_failed(error_message, extra_fields)
        self.assertEqual(self.model.task_status, TaskStatus.FAILED)
        self.assertEqual(self.model.error_message, error_message)
        self.assertEqual(self.model.extra_fields, extra_fields)

    def test_start_processing(self):
        self.model.start_processing()
        self.assertEqual(self.model.task_status, TaskStatus.PROCESSING)
        self.assertIsNotNone(self.model.processed_at)

    def test_update_task_status(self):
        self.model.update_task_status('completed')
        self.assertEqual(self.model.task_status, TaskStatus.COMPLETED)

        self.model.update_task_status('failed', error_message="Error")
        self.assertEqual(self.model.task_status, TaskStatus.FAILED)
        self.assertEqual(self.model.error_message, "Error")

        self.model.update_task_status('cancelled')
        self.assertEqual(self.model.task_status, TaskStatus.CANCELLED)

        self.model.update_task_status('processing')
        self.assertEqual(self.model.task_status, TaskStatus.PROCESSING)

    def test_extra_fields_update(self):
        extra_fields = {'task_id': 'new-task-id'}
        self.model.update_task_status('processing', extra_fields=extra_fields)
        self.assertEqual(self.model.extra_fields['task_id'], 'new-task-id')

    def test_custom_config(self):
        self.assertEqual(self.model.task_config.max_retries, 3)
        self.assertEqual(self.model.task_config.retry_delay, 60)
        self.assertEqual(self.model.task_config.timeout, 300)
        self.assertEqual(self.model.task_config.priority, 1)
        self.assertEqual(self.model.task_config.queue, 'default')

    def test_update_task_status_with_exception(self):
        with self.assertRaises(ValueError):
            self.model.update_task_status('invalid_status') 