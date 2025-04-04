"""
Workflow Engine implementation.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Workflow, Trigger, Action
from .handlers import (
    evaluate_time_trigger,
    evaluate_event_trigger,
    evaluate_data_trigger,
    execute_email_action,
    execute_notification_action,
    execute_webhook_action
)

class WorkflowEngine:
    """
    Core engine for processing workflows, evaluating triggers, and executing actions.
    """
    def __init__(self):
        # Register trigger handlers
        self.trigger_handlers = {
            'time': evaluate_time_trigger,
            'event': evaluate_event_trigger,
            'data': evaluate_data_trigger,
        }
        
        # Register action handlers
        self.action_handlers = {
            'email': execute_email_action,
            'notification': execute_notification_action,
            'webhook': execute_webhook_action,
        }

    def evaluate_trigger_conditions(self, trigger: Trigger, context: dict) -> bool:
        """
        Evaluate trigger conditions using the appropriate handler.
        
        Args:
            trigger: The trigger to evaluate
            context: Context data for evaluation
            
        Returns:
            bool: True if trigger conditions are met, False otherwise
            
        Raises:
            ValidationError: If trigger type is not supported
        """
        handler = self.trigger_handlers.get(trigger.trigger_type)
        if not handler:
            raise ValidationError(_(f'Unsupported trigger type: {trigger.trigger_type}'))
            
        return handler(trigger.conditions, context)

    def execute_action(self, action: Action, context: dict) -> dict:
        """
        Execute an action using the appropriate handler.
        
        Args:
            action: The action to execute
            context: Context data for execution
            
        Returns:
            dict: Result of the action execution
            
        Raises:
            ValidationError: If action type is not supported
        """
        handler = self.action_handlers.get(action.action_type)
        if not handler:
            raise ValidationError(_(f'Unsupported action type: {action.action_type}'))
            
        return handler(action.configuration, context)

    def process_workflow(self, workflow: Workflow, context: dict = None) -> dict:
        """
        Process a workflow by evaluating its triggers and executing corresponding actions.
        
        Args:
            workflow: The workflow to process
            context: Optional context data for processing
            
        Returns:
            dict: Results of workflow processing
            
        Raises:
            ValidationError: If workflow processing fails
        """
        if not workflow.is_active:
            raise ValidationError(_('Cannot process inactive workflow'))
            
        context = context or {}
        results = {
            'workflow_id': workflow.id,
            'trigger_results': [],
            'action_results': []
        }
        
        # Evaluate triggers
        for trigger in workflow.triggers.filter(is_active=True):
            try:
                trigger_result = self.evaluate_trigger_conditions(trigger, context)
                results['trigger_results'].append({
                    'trigger_id': trigger.id,
                    'result': trigger_result
                })
                
                # If trigger conditions are met, execute associated actions
                if trigger_result:
                    for rule in trigger.rules.filter(is_active=True):
                        try:
                            action_result = self.execute_action(rule.action, context)
                            results['action_results'].append({
                                'action_id': rule.action.id,
                                'result': action_result
                            })
                        except Exception as e:
                            results['action_results'].append({
                                'action_id': rule.action.id,
                                'error': str(e)
                            })
                            
            except Exception as e:
                results['trigger_results'].append({
                    'trigger_id': trigger.id,
                    'error': str(e)
                })
                
        return results 