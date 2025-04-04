from celery import shared_task
from django.utils import timezone
from .models import Workflow, Trigger, Action, Report, ReportSchedule, ReportAnalytics
from .engine import WorkflowEngine
from celery.utils.log import get_task_logger
from django.core.exceptions import ValidationError
import json
import time

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

@shared_task
def generate_report(report_id):
    try:
        report = Report.objects.get(id=report_id)
        report.status = 'generating'
        report.save()

        # Record start time for performance tracking
        start_time = time.time()

        # Simulate report generation (replace with actual report generation logic)
        time.sleep(5)  # Simulating work
        report.status = 'completed'
        report.output_path = f'/reports/{report.id}/output.pdf'  # Example path
        report.save()

        # Calculate generation time
        generation_time = time.time() - start_time

        # Update analytics
        analytics, created = ReportAnalytics.objects.get_or_create(template=report.template)
        analytics.total_reports += 1
        analytics.successful_reports += 1
        analytics.success_rate = (analytics.successful_reports / analytics.total_reports) * 100

        # Update performance metrics
        if analytics.average_generation_time is None:
            analytics.average_generation_time = generation_time
        else:
            analytics.average_generation_time = (analytics.average_generation_time + generation_time) / 2

        if analytics.min_generation_time is None or generation_time < analytics.min_generation_time:
            analytics.min_generation_time = generation_time

        if analytics.max_generation_time is None or generation_time > analytics.max_generation_time:
            analytics.max_generation_time = generation_time

        analytics.last_updated = timezone.now()
        analytics.save()

    except Exception as e:
        if 'report' in locals():
            report.status = 'failed'
            report.error_message = str(e)
            report.save()

            # Update analytics for failed report
            if 'analytics' not in locals():
                analytics, created = ReportAnalytics.objects.get_or_create(template=report.template)
            
            analytics.total_reports += 1
            analytics.failed_reports += 1
            analytics.success_rate = (analytics.successful_reports / analytics.total_reports) * 100
            analytics.last_updated = timezone.now()
            analytics.save()

        raise

@shared_task
def process_report_schedules():
    try:
        current_time = timezone.now()
        active_schedules = ReportSchedule.objects.filter(
            is_active=True,
            next_run__lte=current_time
        )

        for schedule in active_schedules:
            try:
                # Create new report from template
                report = Report.objects.create(
                    template=schedule.template,
                    name=f"{schedule.template.name} - Scheduled {current_time.strftime('%Y-%m-%d %H:%M')}",
                    description=f"Automatically generated from schedule {schedule.id}",
                    created_by=schedule.created_by
                )

                # Start report generation
                generate_report.delay(report.id)

                # Update schedule
                schedule.last_run = current_time
                schedule.next_run = schedule.calculate_next_run()
                schedule.save()

                # Update analytics
                analytics, created = ReportAnalytics.objects.get_or_create(template=schedule.template)
                analytics.total_executions += 1
                analytics.successful_executions += 1
                analytics.execution_success_rate = (analytics.successful_executions / analytics.total_executions) * 100
                analytics.last_updated = current_time
                analytics.save()

            except Exception as e:
                # Update analytics for failed execution
                analytics, created = ReportAnalytics.objects.get_or_create(template=schedule.template)
                analytics.total_executions += 1
                analytics.execution_success_rate = (analytics.successful_executions / analytics.total_executions) * 100
                analytics.last_updated = current_time
                analytics.save()

                # Log the error but continue processing other schedules
                print(f"Error processing schedule {schedule.id}: {str(e)}")

    except Exception as e:
        print(f"Error in process_report_schedules: {str(e)}")
        raise 