from unittest.mock import Mock, patch, MagicMock
from celery import Task
from celery.utils.threads import LocalStack
from Core.models.base import TaskConfig, TaskStatus
from Core.tasks.base import BaseTaskWithRetry, ModelTaskMixin
from django.test import TestCase
from django.db import models

class TestModel(models.Model):
    task_status = models.CharField(max_length=20)
    error_message = models.TextField(null=True, blank=True)
    extra_field = models.CharField(max_length=100, null=True)
    objects = Mock()

    class Meta:
        app_label = 'core'

class TestBaseTaskWithRetry(TestCase):
    def setUp(self):
        self.task = BaseTaskWithRetry()
        self.task.name = "test_task"
        self.task.request_stack = LocalStack()
        
        # Create a request context with all necessary attributes
        request_context = {
            'id': "test_id",
            'retries': 0,
            'task': "test_task",
            'called_directly': False,
            'delivery_info': {},
            'headers': None,
            'args': None,
            'kwargs': None,
            'hostname': None,
            'ignore_result': False,
            'callbacks': None,
            'errbacks': None,
            'timelimit': None,
            'eta': None,
            'expires': None,
            'correlation_id': None,
            'reply_to': None,
            'root_id': None,
            'parent_id': None,
            'shadow': None,
            'chain': None,
            'chord': None,
            'group': None,
            'group_index': None,
            'stamped_headers': None,
            'stamps': None,
            'is_eager': False,
            'logfile': None,
            'loglevel': None,
            'origin': None,
            'properties': None,
            'replaced_task_nesting': 0,
        }
        
        # Push the request context onto the stack
        self.task.push_request(**request_context)

    def test_apply_async(self):
        args = ('arg1', 'arg2')
        kwargs = {'kwarg1': 'value1'}
        
        with patch.object(Task, 'apply_async') as mock_apply_async:
            self.task.apply_async(args=args, kwargs=kwargs)
            mock_apply_async.assert_called_once_with(args=args, kwargs=kwargs)

    @patch('Core.tasks.base.logger')
    def test_on_failure(self, mock_logger):
        exc = ValueError("Test error")
        task_id = 'test-task-id'
        args = ('arg1', 'arg2')
        kwargs = {'kwarg1': 'value1'}
        einfo = Mock()
        
        self.task.on_failure(exc, task_id, args, kwargs, einfo)
        
        mock_logger.error.assert_called_once_with(
            f"Task {task_id} failed: {exc}\nArgs: {args}\nKwargs: {kwargs}",
            exc_info=einfo
        )

    @patch('Core.tasks.base.logger')
    def test_on_success(self, mock_logger):
        retval = {'result': 'success'}
        task_id = 'test-task-id'
        args = ('arg1', 'arg2')
        kwargs = {'kwarg1': 'value1'}
        
        self.task.on_success(retval, task_id, args, kwargs)
        
        mock_logger.info.assert_called_once_with(f"Task {task_id} completed successfully")

class TestModelTaskMixin(TestCase):
    def setUp(self):
        self.mixin = ModelTaskMixin()
        self.model_class = TestModel
        self.instance_id = 1

    def test_get_model_instance_success(self):
        mock_instance = Mock(spec=TestModel)
        with patch.object(TestModel.objects, 'get', return_value=mock_instance):
            result = self.mixin.get_model_instance(TestModel, self.instance_id)
            self.assertEqual(result, mock_instance)

    def test_get_model_instance_not_found(self):
        with patch.object(TestModel.objects, 'get', side_effect=TestModel.DoesNotExist):
            result = self.mixin.get_model_instance(TestModel, self.instance_id)
            self.assertIsNone(result)

    def test_get_model_instance_error(self):
        with patch.object(TestModel.objects, 'get', side_effect=Exception("Test error")):
            result = self.mixin.get_model_instance(TestModel, self.instance_id)
            self.assertIsNone(result)

    def test_update_model_status_success(self):
        mock_instance = Mock(spec=TestModel)
        mock_instance.save = Mock()
        
        result = self.mixin.update_model_status(
            mock_instance,
            'status',
            'new_status',
            {'extra_field': 'value'}
        )
        
        self.assertTrue(result)
        self.assertEqual(mock_instance.status, 'new_status')
        self.assertEqual(mock_instance.extra_field, 'value')
        mock_instance.save.assert_called_once_with(update_fields=['status', 'extra_field'])

    def test_update_model_status_error(self):
        mock_instance = Mock(spec=TestModel)
        mock_instance.save.side_effect = Exception("Test error")
        
        result = self.mixin.update_model_status(
            mock_instance,
            'status',
            'new_status'
        )
        
        self.assertFalse(result)

class TestTaskWithModelMixin(TestCase):
    def setUp(self):
        class TestTaskWithModel(BaseTaskWithRetry, ModelTaskMixin):
            def run(self, instance_id):
                instance = self.get_model_instance(TestModel, instance_id)
                if not instance:
                    return None
                
                try:
                    self.update_model_status(instance, 'task_status', TaskStatus.PROCESSING)
                    # Simulate task processing
                    self.update_model_status(instance, 'task_status', TaskStatus.COMPLETED)
                    return instance
                except Exception as e:
                    self.update_model_status(
                        instance,
                        'task_status',
                        TaskStatus.FAILED,
                        {'error_message': str(e)}
                    )
                    raise
        
        self.task = TestTaskWithModel()
        self.task.name = "test_task"
        self.task.request_stack = LocalStack()
        
        # Create a request context with all necessary attributes
        request_context = {
            'id': "test_id",
            'retries': 0,
            'task': "test_task",
            'called_directly': False,
            'delivery_info': {},
            'headers': None,
            'args': None,
            'kwargs': None,
            'hostname': None,
            'ignore_result': False,
            'callbacks': None,
            'errbacks': None,
            'timelimit': None,
            'eta': None,
            'expires': None,
            'correlation_id': None,
            'reply_to': None,
            'root_id': None,
            'parent_id': None,
            'shadow': None,
            'chain': None,
            'chord': None,
            'group': None,
            'group_index': None,
            'stamped_headers': None,
            'stamps': None,
            'is_eager': False,
            'logfile': None,
            'loglevel': None,
            'origin': None,
            'properties': None,
            'replaced_task_nesting': 0,
        }
        
        # Push the request context onto the stack
        self.task.push_request(**request_context)
        
        # Set up the test model
        self.model = TestModel()
        self.model.id = 1
        self.model.task_status = TaskStatus.PENDING
        self.model.error_message = None
        self.model.save = Mock()

    def test_task_successful_execution(self):
        with patch.object(ModelTaskMixin, 'get_model_instance', return_value=self.model):
            result = self.task.run(self.model.id)
            self.assertEqual(result, self.model)
            self.assertEqual(self.model.task_status, TaskStatus.COMPLETED)

    def test_task_invalid_model_id(self):
        with patch.object(ModelTaskMixin, 'get_model_instance', return_value=None):
            result = self.task.run(999)
            self.assertIsNone(result)

    def test_task_retry_on_error(self):
        def side_effect(*args, **kwargs):
            raise Exception("Test error")

        with patch.object(ModelTaskMixin, 'get_model_instance', return_value=self.model), \
             patch.object(ModelTaskMixin, 'update_model_status', side_effect=side_effect):
            with self.assertRaises(Exception):
                self.task.run(self.model.id) 