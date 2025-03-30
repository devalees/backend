import pytest
from django.test import TestCase
from django.utils import timezone
from Core.models.base import TaskAwareModel, TaskStatus, TaskConfig
from django.db import models
from datetime import timedelta

class TestModel(TaskAwareModel):
    name = models.CharField(max_length=100)
    extra_field = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        app_label = 'core'

class CustomConfigModel(TaskAwareModel):
    name = models.CharField(max_length=100)
    custom_status = models.CharField(max_length=20, default='pending')
    custom_error = models.TextField(null=True)
    custom_processed = models.DateTimeField(null=True)
    custom_task_id = models.CharField(max_length=255, null=True)

    task_config = TaskConfig(
        status_field='custom_status',
        error_field='custom_error',
        processed_at_field='custom_processed',
        task_id_field='custom_task_id'
    )

    class Meta:
        app_label = 'core'

class TestTaskAwareModel(TestCase):
    def setUp(self):
        self.model = TestModel.objects.create(name='test')
        self.custom_model = CustomConfigModel.objects.create(name='custom')

    def test_initial_status(self):
        """Test that model initializes with PENDING status"""
        self.assertEqual(self.model.task_status, TaskStatus.PENDING.value)
        self.assertIsNone(self.model.task_id)
        self.assertIsNone(self.model.error_message)
        self.assertIsNone(self.model.processed_at)

    def test_start_processing(self):
        """Test start_processing method"""
        task_id = 'test-task-123'
        success = self.model.start_processing(task_id=task_id)
        
        self.assertTrue(success)
        self.assertEqual(self.model.task_status, TaskStatus.PROCESSING.value)
        self.assertEqual(self.model.task_id, task_id)

    def test_mark_completed(self):
        """Test mark_completed method"""
        success = self.model.mark_completed(extra_field='value')
        
        self.assertTrue(success)
        self.assertEqual(self.model.task_status, TaskStatus.COMPLETED.value)
        self.assertIsNotNone(self.model.processed_at)
        self.assertTrue(timezone.now() - self.model.processed_at < timedelta(seconds=1))
        self.assertEqual(self.model.extra_field, 'value')

    def test_mark_failed(self):
        """Test mark_failed method"""
        error_msg = 'Test error message'
        success = self.model.mark_failed(error_msg, extra_field='value')
        
        self.assertTrue(success)
        self.assertEqual(self.model.task_status, TaskStatus.FAILED.value)
        self.assertEqual(self.model.error_message, error_msg)
        self.assertEqual(self.model.extra_field, 'value')

    def test_status_properties(self):
        """Test is_processing, is_completed, and is_failed properties"""
        self.model.start_processing()
        self.assertTrue(self.model.is_processing)
        self.assertFalse(self.model.is_completed)
        self.assertFalse(self.model.is_failed)

        self.model.mark_completed()
        self.assertFalse(self.model.is_processing)
        self.assertTrue(self.model.is_completed)
        self.assertFalse(self.model.is_failed)

        self.model.mark_failed('error')
        self.assertFalse(self.model.is_processing)
        self.assertFalse(self.model.is_completed)
        self.assertTrue(self.model.is_failed)

    def test_custom_config(self):
        """Test model with custom task configuration"""
        task_id = 'custom-task-123'
        self.custom_model.start_processing(task_id=task_id)
        
        self.assertEqual(self.custom_model.custom_status, TaskStatus.PROCESSING.value)
        self.assertEqual(self.custom_model.custom_task_id, task_id)

        self.custom_model.mark_completed()
        self.assertEqual(self.custom_model.custom_status, TaskStatus.COMPLETED.value)
        self.assertIsNotNone(self.custom_model.custom_processed)

        error_msg = 'Custom error'
        self.custom_model.mark_failed(error_msg)
        self.assertEqual(self.custom_model.custom_status, TaskStatus.FAILED.value)
        self.assertEqual(self.custom_model.custom_error, error_msg)

    def test_update_task_status_with_exception(self):
        """Test update_task_status method when an exception occurs"""
        # Create a model instance that will raise an exception when saved
        model = TestModel.objects.create(name='test_exception')
        
        # Mock the save method to raise an exception
        def mock_save(*args, **kwargs):
            raise Exception('Test exception')
        
        model.save = mock_save
        
        # Test that the method returns False when an exception occurs
        success = model.update_task_status(TaskStatus.COMPLETED)
        self.assertFalse(success)

    def test_extra_fields_update(self):
        """Test updating extra fields with task status"""
        # Add some extra fields when marking as completed
        extra_fields = {
            'task_id': 'new-task-id',
            'error_message': 'previous error',
            'extra_field': 'test value'
        }
        
        success = self.model.mark_completed(**extra_fields)
        
        self.assertTrue(success)
        self.assertEqual(self.model.task_id, 'new-task-id')
        self.assertEqual(self.model.error_message, 'previous error')
        self.assertEqual(self.model.task_status, TaskStatus.COMPLETED.value)
        self.assertEqual(self.model.extra_field, 'test value') 