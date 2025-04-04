from celery import shared_task
from django.utils import timezone
from .models import Workflow, Trigger, Action
from .engine import WorkflowEngine
from celery.utils.log import get_task_logger
from django.core.exceptions import ValidationError
import json

logger = get_task_logger(__name__)

@shared_task(
    name='automation.tasks.process_workflow',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue='high_priority'
)
def process_workflow(self, workflow_id, context=None):
    """
    Process a workflow asynchronously.
    
    Args:
        workflow_id (int): ID of the workflow to process
        context (dict, optional): Additional context for workflow processing
    """
    try:
        workflow = Workflow.objects.get(id=workflow_id)
        engine = WorkflowEngine()
        
        # Update workflow status to running
        workflow.task_status = 'running'
        workflow.save()
        
        # Process the workflow
        result = engine.process_workflow(workflow, context or {})
        
        # Update workflow with results
        workflow.task_status = 'completed'
        workflow.task_result = json.dumps(result)
        workflow.last_run = timezone.now()
        workflow.save()
        
        return result
        
    except Workflow.DoesNotExist:
        logger.error(f"Workflow {workflow_id} not found")
        raise
    except ValidationError as e:
        logger.error(f"Validation error in workflow {workflow_id}: {str(e)}")
        workflow.task_status = 'error'
        workflow.error_message = str(e)
        workflow.save()
        raise
    except Exception as e:
        logger.error(f"Error processing workflow {workflow_id}: {str(e)}")
        workflow.task_status = 'error'
        workflow.error_message = str(e)
        workflow.save()
        self.retry(exc=e)

@shared_task(
    name='automation.tasks.schedule_workflows',
    bind=True,
    queue='low_priority'
)
def schedule_workflows(self):
    """
    Periodic task to check and schedule time-based workflows.
    """
    try:
        # Get all active workflows with time-based triggers
        workflows = Workflow.objects.filter(
            is_active=True,
            triggers__trigger_type='time'
        ).prefetch_related('triggers')
        
        for workflow in workflows:
            try:
                # Get the first time-based trigger for this workflow
                trigger = workflow.triggers.filter(trigger_type='time').first()
                if not trigger:
                    continue
                    
                engine = WorkflowEngine()
                
                # Check if workflow should be triggered
                if engine.evaluate_trigger_conditions(trigger, {}):
                    # Schedule workflow processing
                    process_workflow.delay(workflow.id)
                    
                    logger.info(f"Scheduled workflow {workflow.id} for processing")
                    
            except Exception as e:
                logger.error(f"Error scheduling workflow {workflow.id}: {str(e)}")
                continue
                
        return f"Processed {len(workflows)} workflows"
        
    except Exception as e:
        logger.error(f"Error in schedule_workflows task: {str(e)}")
        raise

@shared_task(
    name='automation.tasks.cleanup_workflows',
    bind=True,
    queue='low_priority'
)
def cleanup_workflows(self):
    """
    Periodic task to clean up old workflow results and error messages.
    """
    try:
        # Clean up workflows older than 30 days
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        workflows = Workflow.objects.filter(
            last_run__lt=cutoff_date,
            task_status__in=['completed', 'error']
        )
        
        for workflow in workflows:
            workflow.task_result = None
            workflow.error_message = None
            workflow.save()
            
        return f"Cleaned up {len(workflows)} workflows"
        
    except Exception as e:
        logger.error(f"Error in cleanup_workflows task: {str(e)}")
        raise 