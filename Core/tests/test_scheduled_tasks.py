from django.test import TestCase
from celery import Celery
from unittest.mock import patch, MagicMock
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from Apps.tasks.scheduled import test_scheduled_task

class TestScheduledTasks(TestCase):
    def setUp(self):
        self.app = Celery('test_app')
        self.mock_logger = MagicMock()
        
        # Create a test interval schedule
        self.schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES
        )
        
        # Create a test periodic task
        self.periodic_task = PeriodicTask.objects.create(
            name='test_scheduled_task',
            task='Apps.tasks.scheduled.test_scheduled_task',
            interval=self.schedule,
            enabled=True
        )

    def test_scheduled_task_creation(self):
        """Test that a scheduled task is properly created"""
        self.assertEqual(self.periodic_task.name, 'test_scheduled_task')
        self.assertEqual(self.periodic_task.task, 'Apps.tasks.scheduled.test_scheduled_task')
        self.assertTrue(self.periodic_task.enabled)

    def test_scheduled_task_execution(self):
        """Test that a scheduled task executes properly"""
        with patch.object(test_scheduled_task, 'apply_async') as mock_apply:
            # Simulate task execution
            test_scheduled_task.apply_async()
            mock_apply.assert_called_once()
            
            # Verify the result
            args, kwargs = mock_apply.call_args
            self.assertEqual(kwargs.get('queue'), 'default')

    def test_scheduled_task_disabling(self):
        """Test that a scheduled task can be disabled"""
        self.periodic_task.enabled = False
        self.periodic_task.save()
        self.assertFalse(self.periodic_task.enabled)

    def test_scheduled_task_schedule_modification(self):
        """Test that a scheduled task's schedule can be modified"""
        new_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES
        )
        self.periodic_task.interval = new_schedule
        self.periodic_task.save()
        
        self.assertEqual(self.periodic_task.interval.every, 5)
        self.assertEqual(self.periodic_task.interval.period, IntervalSchedule.MINUTES)

    def test_scheduled_task_cleanup(self):
        """Test that scheduled tasks can be properly cleaned up"""
        self.periodic_task.delete()
        self.assertEqual(PeriodicTask.objects.count(), 0) 