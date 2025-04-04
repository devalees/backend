import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from Apps.automation.models import (
    Workflow,
    Trigger,
    TriggerExecution,
    TriggerMetrics
)
from Apps.automation.engine import WorkflowEngine

User = get_user_model()

@pytest.mark.django_db
class TestTriggerMonitoring:
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def workflow(self, test_user):
        """Create a test workflow"""
        return Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for monitoring",
            created_by=test_user
        )

    @pytest.fixture
    def trigger(self, workflow, test_user):
        """Create a test trigger"""
        return Trigger.objects.create(
            name="Test Trigger",
            workflow=workflow,
            trigger_type="time",
            conditions={"schedule": "daily"},
            created_by=test_user
        )

    def test_create_trigger_execution(self, trigger):
        """Test creating a trigger execution record"""
        execution = TriggerExecution.objects.create(
            trigger=trigger,
            started_at=timezone.now(),
            status='processing'
        )

        assert execution.trigger == trigger
        assert execution.status == 'processing'
        assert execution.started_at is not None
        assert execution.completed_at is None
        assert execution.execution_time is None
        assert execution.error_message is None

    def test_complete_trigger_execution(self, trigger):
        """Test completing a trigger execution"""
        started_at = timezone.now()
        execution = TriggerExecution.objects.create(
            trigger=trigger,
            started_at=started_at,
            status='processing'
        )

        # Complete the execution
        execution.complete_execution(status='completed')
        
        assert execution.status == 'completed'
        assert execution.completed_at is not None
        assert execution.execution_time > 0
        assert execution.error_message is None

    def test_failed_trigger_execution(self, trigger):
        """Test failed trigger execution"""
        execution = TriggerExecution.objects.create(
            trigger=trigger,
            started_at=timezone.now(),
            status='processing'
        )

        error_message = "Test error message"
        execution.complete_execution(status='failed', error_message=error_message)
        
        assert execution.status == 'failed'
        assert execution.completed_at is not None
        assert execution.execution_time > 0
        assert execution.error_message == error_message

    def test_trigger_metrics_calculation(self, trigger):
        """Test trigger metrics calculation"""
        # Create multiple executions
        for _ in range(3):
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                started_at=timezone.now(),
                status='processing'
            )
            execution.complete_execution(status='completed')

        # Create a failed execution
        failed_execution = TriggerExecution.objects.create(
            trigger=trigger,
            started_at=timezone.now(),
            status='processing'
        )
        failed_execution.complete_execution(status='failed', error_message='Test error')

        # Calculate metrics
        metrics = TriggerMetrics.calculate_metrics(trigger)
        
        assert metrics.total_executions == 4
        assert metrics.successful_executions == 3
        assert metrics.failed_executions == 1
        assert metrics.success_rate == 75.0  # 3/4 * 100
        assert metrics.average_execution_time > 0
        assert metrics.last_execution_status == 'failed'
        assert metrics.last_execution_time is not None

    def test_trigger_health_check(self, trigger):
        """Test trigger health check"""
        # Create successful executions
        for _ in range(3):
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                started_at=timezone.now(),
                status='processing'
            )
            execution.complete_execution(status='completed')

        health_status = TriggerMetrics.check_trigger_health(trigger)
        assert health_status['status'] == 'healthy'
        assert health_status['success_rate'] == 100.0
        assert health_status['recent_failures'] == 0

        # Add some failures
        for _ in range(2):
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                started_at=timezone.now(),
                status='processing'
            )
            execution.complete_execution(status='failed', error_message='Test error')

        health_status = TriggerMetrics.check_trigger_health(trigger)
        assert health_status['status'] == 'critical'
        assert health_status['success_rate'] == 60.0  # 3/5 * 100
        assert health_status['recent_failures'] == 2

    def test_trigger_execution_cleanup(self, trigger):
        """Test cleanup of old trigger executions"""
        # Create old executions
        old_date = timezone.now() - timezone.timedelta(days=31)
        for _ in range(3):
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                started_at=old_date,
                status='completed'
            )
            execution.completed_at = old_date + timezone.timedelta(minutes=5)
            execution.save()

        # Create recent executions
        for _ in range(2):
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                started_at=timezone.now(),
                status='completed'
            )
            execution.complete_execution(status='completed')

        # Cleanup old executions
        deleted_count = TriggerExecution.cleanup_old_executions(days=30)
        
        assert deleted_count == 3
        assert TriggerExecution.objects.count() == 2 