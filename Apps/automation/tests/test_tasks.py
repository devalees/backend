import pytest
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from Apps.automation.models import Workflow, Trigger, Action
from Apps.automation.tasks import process_workflow, schedule_workflows, cleanup_workflows
from Apps.automation.engine import WorkflowEngine
import json

User = get_user_model()

@pytest.mark.django_db
class TestAutomationTasks:
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
        """Create a test workflow with trigger and action"""
        workflow = Workflow.objects.create(
            name="Test Workflow",
            description="Test workflow for task processing",
            created_by=test_user,
            is_active=True
        )
        
        trigger = Trigger.objects.create(
            workflow=workflow,
            trigger_type="time",
            name="Test Trigger",
            conditions={"schedule": "daily"},
            created_by=test_user
        )
        
        action = Action.objects.create(
            workflow=workflow,
            action_type="email",
            name="Test Action",
            configuration={"to": "test@example.com"},
            created_by=test_user
        )
        
        return workflow

    @pytest.mark.celery(result_backend='django-db')
    def test_process_workflow_success(self, workflow):
        """Test successful workflow processing"""
        with patch.object(WorkflowEngine, 'process_workflow') as mock_process:
            # Setup mock return value
            mock_result = {"status": "success", "action_results": ["email_sent"]}
            mock_process.return_value = mock_result
            
            # Process workflow
            result = process_workflow(workflow.id)
            
            # Verify workflow was processed
            mock_process.assert_called_once()
            
            # Verify workflow status was updated
            workflow.refresh_from_db()
            assert workflow.task_status == 'completed'
            assert json.loads(workflow.task_result) == mock_result
            assert workflow.last_run is not None
            assert workflow.error_message is None

    @pytest.mark.celery(result_backend='django-db')
    def test_process_workflow_error(self, workflow):
        """Test workflow processing with error"""
        with patch.object(WorkflowEngine, 'process_workflow') as mock_process:
            # Setup mock to raise exception
            mock_process.side_effect = ValueError("Test error")
            
            # Process workflow should retry
            with pytest.raises(ValueError):
                process_workflow(workflow.id)
            
            # Verify workflow status was updated
            workflow.refresh_from_db()
            assert workflow.task_status == 'error'
            assert workflow.error_message == "Test error"

    @pytest.mark.celery(result_backend='django-db')
    def test_schedule_workflows(self, workflow):
        """Test workflow scheduling task"""
        with patch.object(WorkflowEngine, 'evaluate_trigger_conditions') as mock_evaluate:
            with patch('Apps.automation.tasks.process_workflow.delay') as mock_delay:
                # Setup mock to return True for trigger evaluation
                mock_evaluate.return_value = True
                
                # Run scheduling task
                result = schedule_workflows()
                
                # Verify trigger was evaluated
                mock_evaluate.assert_called_once()
                
                # Verify workflow was scheduled
                mock_delay.assert_called_once_with(workflow.id)
                
                assert "Processed 1 workflows" in result

    @pytest.mark.celery(result_backend='django-db')
    def test_schedule_workflows_no_triggers(self, workflow):
        """Test workflow scheduling with no eligible workflows"""
        # Deactivate workflow
        workflow.is_active = False
        workflow.save()
        
        # Run scheduling task
        result = schedule_workflows()
        
        # Verify no workflows were processed
        assert "Processed 0 workflows" in result

    @pytest.mark.celery(result_backend='django-db')
    def test_cleanup_workflows(self, workflow):
        """Test workflow cleanup task"""
        # Setup workflow with old results
        workflow.task_status = 'completed'
        workflow.task_result = json.dumps({"status": "success"})
        workflow.error_message = "Old error"
        workflow.last_run = timezone.now() - timezone.timedelta(days=31)
        workflow.save()
        
        # Run cleanup task
        result = cleanup_workflows()
        
        # Verify workflow was cleaned up
        workflow.refresh_from_db()
        assert workflow.task_result is None
        assert workflow.error_message is None
        assert "Cleaned up 1 workflows" in result

    @pytest.mark.celery(result_backend='django-db')
    def test_cleanup_workflows_recent(self, workflow):
        """Test workflow cleanup task with recent workflows"""
        # Setup workflow with recent results
        workflow.task_status = 'completed'
        workflow.task_result = json.dumps({"status": "success"})
        workflow.error_message = "Recent error"
        workflow.last_run = timezone.now() - timezone.timedelta(days=1)
        workflow.save()
        
        # Run cleanup task
        result = cleanup_workflows()
        
        # Verify workflow was not cleaned up
        workflow.refresh_from_db()
        assert workflow.task_result is not None
        assert workflow.error_message is not None
        assert "Cleaned up 0 workflows" in result