"""
Handlers for workflow triggers and actions.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import requests
import json
from typing import Dict, Any

def evaluate_time_trigger(conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate time-based trigger conditions.
    
    Args:
        conditions: Dictionary containing schedule configuration
        context: Context data for evaluation
        
    Returns:
        bool: True if conditions are met, False otherwise
    """
    schedule = conditions.get('schedule')
    if not schedule:
        return False
        
    now = timezone.now()
    
    if schedule == 'daily':
        time_str = conditions.get('time', '00:00')
        hour, minute = map(int, time_str.split(':'))
        return now.hour == hour and now.minute == minute
        
    elif schedule == 'weekly':
        day = conditions.get('day', 0)  # 0 = Monday
        time_str = conditions.get('time', '00:00')
        hour, minute = map(int, time_str.split(':'))
        return now.weekday() == day and now.hour == hour and now.minute == minute
        
    elif schedule == 'monthly':
        day = conditions.get('day', 1)
        time_str = conditions.get('time', '00:00')
        hour, minute = map(int, time_str.split(':'))
        return now.day == day and now.hour == hour and now.minute == minute
        
    return False

def evaluate_event_trigger(conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate event-based trigger conditions.
    
    Args:
        conditions: Dictionary containing event configuration
        context: Context data for evaluation
        
    Returns:
        bool: True if conditions are met, False otherwise
    """
    event_type = conditions.get('event_type')
    if not event_type:
        return False
        
    # Check if the event type matches
    if event_type != context.get('event_type'):
        return False
        
    # Check field conditions if any
    field_conditions = conditions.get('field_conditions', {})
    for field, value in field_conditions.items():
        if context.get(field) != value:
            return False
            
    return True

def evaluate_data_trigger(conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate data-based trigger conditions.
    
    Args:
        conditions: Dictionary containing data conditions
        context: Context data for evaluation
        
    Returns:
        bool: True if conditions are met, False otherwise
    """
    # Placeholder for data trigger evaluation
    # This would typically involve checking data conditions against a database or external source
    return True

def execute_email_action(configuration: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an email action.
    
    Args:
        configuration: Dictionary containing email configuration
        context: Context data for execution
        
    Returns:
        dict: Result of the email sending operation
    """
    to_email = configuration.get('to')
    subject = configuration.get('subject', 'Workflow Notification')
    message = configuration.get('message', '')
    
    # Format message with context variables
    try:
        message = message.format(**context)
    except KeyError:
        pass
    
    # Send email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )
    
    return {
        'status': 'success',
        'to': to_email,
        'subject': subject
    }

def execute_notification_action(configuration: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a notification action.
    
    Args:
        configuration: Dictionary containing notification configuration
        context: Context data for execution
        
    Returns:
        dict: Result of the notification operation
    """
    # Placeholder for notification implementation
    return {
        'status': 'success',
        'type': 'notification',
        'message': configuration.get('message', '')
    }

def execute_webhook_action(configuration: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a webhook action.
    
    Args:
        configuration: Dictionary containing webhook configuration
        context: Context data for execution
        
    Returns:
        dict: Result of the webhook operation
    """
    url = configuration.get('url')
    method = configuration.get('method', 'POST')
    headers = configuration.get('headers', {})
    payload = configuration.get('payload', {})
    
    # Format payload with context variables
    try:
        payload = json.loads(json.dumps(payload).format(**context))
    except KeyError:
        pass
    
    # Make HTTP request
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=payload,
        timeout=30
    )
    
    return {
        'status': 'success' if response.ok else 'error',
        'status_code': response.status_code,
        'response': response.text
    } 