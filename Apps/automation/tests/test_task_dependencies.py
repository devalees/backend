import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.automation.models import Workflow, TaskDependency, Task
from datetime import timedelta

User = get_user_model()

class TestTaskDependencies(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            created_by=self.user
        )
        
        # Create test tasks
        self.task1 = Task.objects.create(
            name='Task 1',
            workflow=self.workflow,
            created_by=self.user,
            task_status='pending'
        )
        self.task2 = Task.objects.create(
            name='Task 2',
            workflow=self.workflow,
            created_by=self.user,
            task_status='pending'
        )
        self.task3 = Task.objects.create(
            name='Task 3',
            workflow=self.workflow,
            created_by=self.user,
            task_status='pending'
        )

    def test_create_task_dependency(self):
        """Test creating a valid task dependency"""
        dependency = TaskDependency.objects.create(
            dependent_task=self.task2,
            dependency_task=self.task1
        )
        self.assertEqual(dependency.dependent_task, self.task2)
        self.assertEqual(dependency.dependency_task, self.task1)

    def test_prevent_self_dependency(self):
        """Test that a task cannot depend on itself"""
        with self.assertRaises(ValidationError):
            TaskDependency.objects.create(
                dependent_task=self.task1,
                dependency_task=self.task1
            )

    def test_prevent_circular_dependency_direct(self):
        """Test prevention of direct circular dependencies"""
        TaskDependency.objects.create(
            dependent_task=self.task2,
            dependency_task=self.task1
        )
        
        with self.assertRaises(ValidationError):
            TaskDependency.objects.create(
                dependent_task=self.task1,
                dependency_task=self.task2
            )

    def test_prevent_circular_dependency_indirect(self):
        """Test prevention of indirect circular dependencies"""
        # Create chain: task1 -> task2 -> task3
        TaskDependency.objects.create(
            dependent_task=self.task2,
            dependency_task=self.task1
        )
        TaskDependency.objects.create(
            dependent_task=self.task3,
            dependency_task=self.task2
        )
        
        # Attempt to create circular dependency: task3 -> task1
        with self.assertRaises(ValidationError):
            TaskDependency.objects.create(
                dependent_task=self.task1,
                dependency_task=self.task3
            )

    def test_check_dependencies_satisfied(self):
        """Test checking if task dependencies are satisfied"""
        # Create dependency: task2 depends on task1
        TaskDependency.objects.create(
            dependent_task=self.task2,
            dependency_task=self.task1
        )
        
        # Initially task1 is pending, so task2's dependencies are not satisfied
        self.assertFalse(self.task2.are_dependencies_satisfied())
        
        # Complete task1
        self.task1.task_status = 'completed'
        self.task1.save()
        
        # Now task2's dependencies should be satisfied
        self.assertTrue(self.task2.are_dependencies_satisfied())

    def test_check_multiple_dependencies(self):
        """Test checking multiple dependencies for a task"""
        # Task3 depends on both task1 and task2
        TaskDependency.objects.create(
            dependent_task=self.task3,
            dependency_task=self.task1
        )
        TaskDependency.objects.create(
            dependent_task=self.task3,
            dependency_task=self.task2
        )
        
        # Initially no dependencies are satisfied
        self.assertFalse(self.task3.are_dependencies_satisfied())
        
        # Complete task1
        self.task1.task_status = 'completed'
        self.task1.save()
        
        # Still not satisfied because task2 is pending
        self.assertFalse(self.task3.are_dependencies_satisfied())
        
        # Complete task2
        self.task2.task_status = 'completed'
        self.task2.save()
        
        # Now all dependencies should be satisfied
        self.assertTrue(self.task3.are_dependencies_satisfied())

    def test_get_dependency_chain(self):
        """Test getting the full dependency chain for a task"""
        # Create chain: task1 -> task2 -> task3
        TaskDependency.objects.create(
            dependent_task=self.task2,
            dependency_task=self.task1
        )
        TaskDependency.objects.create(
            dependent_task=self.task3,
            dependency_task=self.task2
        )
        
        # Get dependency chain for task3
        chain = self.task3.get_dependency_chain()
        
        # Chain should contain task1 and task2 in correct order
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0], self.task1)
        self.assertEqual(chain[1], self.task2) 