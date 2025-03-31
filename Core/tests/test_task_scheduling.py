from django.test import TestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from celery import Celery, shared_task
from datetime import timedelta
from unittest.mock import patch, MagicMock
from celery.schedules import crontab, schedule
from Core.models.test_models import TestTaskAwareModel, TestTaskConfig
import json

class TestTaskScheduling(TestCase):
    def setUp(self):
        self.app = Celery('test')
        self.app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )
        self.config = TestTaskConfig.objects.create()
        self.model = TestTaskAwareModel.objects.create(
            name='test_model',
            task_config=self.config
        )
        self.task = self.app.task(lambda: 1)

    def test_interval_schedule(self):
        """Test creating a periodic task with an interval schedule."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_interval_task',
            task='test_task',
            interval=interval
        )
        self.assertEqual(task.interval.every, 10)

    def test_crontab_schedule(self):
        """Test creating a periodic task with a crontab schedule."""
        crontab_schedule = CrontabSchedule.objects.create(
            hour=8,
            minute=30
        )
        task = PeriodicTask.objects.create(
            name='test_crontab_task',
            task='test_task',
            crontab=crontab_schedule
        )
        self.assertEqual(task.crontab.hour, '8')
        self.assertEqual(task.crontab.minute, '30')

    def test_periodic_task_creation(self):
        """Test creating a periodic task."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )
        self.assertTrue(task.enabled)

    def test_periodic_task_enable_disable(self):
        """Test enabling and disabling a periodic task."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )
        self.assertTrue(task.enabled)
        task.enabled = False
        task.save()
        self.assertFalse(task.enabled)
        task.enabled = True
        task.save()
        self.assertTrue(task.enabled)

    def test_periodic_task_last_run(self):
        """Test getting the last run time of a periodic task."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )
        self.assertIsNone(task.last_run_at)

    def test_periodic_task_total_run_count(self):
        """Test getting the total run count of a periodic task."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )
        self.assertEqual(task.total_run_count, 0)

    def test_periodic_task_schedule_next_run(self):
        """Test getting the next run time of a periodic task."""
        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )
        next_run = task.schedule.next()
        self.assertIsNotNone(next_run)

    def test_periodic_task_execution(self):
        """Test executing a periodic task."""
        @self.app.task(name='test_task')
        def test_task():
            return 1

        interval = IntervalSchedule.objects.create(every=10, period='seconds')
        task = PeriodicTask.objects.create(
            name='test_task',
            task='test_task',
            interval=interval
        )

        with patch.object(test_task, 'apply_async') as mock_apply:
            task.run()
            mock_apply.assert_called_once() 