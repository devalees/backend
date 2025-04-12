"""
Audit Monitoring Operations

This module provides functionality for monitoring the audit system,
including metrics collection, alert generation, and reporting.
"""

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q, Min, Max

from Apps.rbac.models import Audit, OrganizationMonitor

# Constants for monitoring thresholds
AUDIT_LOG_COUNT_THRESHOLD = 1000  # Alert if more than 1000 audit logs per day
AUDIT_ERROR_RATE_THRESHOLD = 0.1  # Alert if error rate exceeds 10%
AUDIT_RESPONSE_TIME_THRESHOLD = 500  # Alert if response time exceeds 500ms

def monitor_audit_log_count(organization, organization_context):
    """
    Monitor the count of audit logs for an organization.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        OrganizationMonitor: The created monitor instance
    """
    # Count audit logs in the last 24 hours
    count = Audit.objects.filter(
        organization=organization,
        timestamp__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    # Create or update the monitor
    monitor, _ = OrganizationMonitor.objects.update_or_create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_log_count',
        defaults={
            'metric_value': count,
            'metric_type': 'counter',
            'timestamp': timezone.now()
        }
    )
    
    return monitor

def monitor_audit_error_rate(organization, organization_context):
    """
    Monitor the error rate of audit logs for an organization.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        OrganizationMonitor: The created monitor instance
    """
    # Get audit logs in the last 24 hours
    audits = Audit.objects.filter(
        organization=organization,
        timestamp__gte=timezone.now() - timedelta(days=1)
    )
    
    total_count = audits.count()
    if total_count == 0:
        error_rate = 0
    else:
        error_count = audits.filter(status='failed').count()
        error_rate = error_count / total_count
    
    # Create or update the monitor
    monitor, _ = OrganizationMonitor.objects.update_or_create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_error_rate',
        defaults={
            'metric_value': error_rate,
            'metric_type': 'gauge',
            'timestamp': timezone.now()
        }
    )
    
    return monitor

def monitor_audit_response_time(organization, organization_context):
    """
    Monitor the average response time of audit operations.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        OrganizationMonitor: The created monitor instance
    """
    # Get audit logs with response times in the last 24 hours
    audits = Audit.objects.filter(
        organization=organization,
        timestamp__gte=timezone.now() - timedelta(days=1),
        details__has_key='response_time'
    )
    
    # Calculate average response time
    # Use a more direct approach to avoid JSON field issues
    total_time = 0
    count = 0
    for audit in audits:
        if 'response_time' in audit.details:
            total_time += audit.details['response_time']
            count += 1
    
    avg_response_time = total_time / count if count > 0 else 0
    
    # Create or update the monitor
    monitor, _ = OrganizationMonitor.objects.update_or_create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_response_time',
        defaults={
            'metric_value': avg_response_time,
            'metric_type': 'histogram',
            'timestamp': timezone.now()
        }
    )
    
    return monitor

def generate_audit_alerts(organization, organization_context):
    """
    Generate alerts based on audit monitoring metrics.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        list: List of generated alerts
    """
    alerts = []
    
    # Get the latest monitors
    monitors = OrganizationMonitor.objects.filter(
        organization=organization,
        organization_context=organization_context,
        timestamp__gte=timezone.now() - timedelta(hours=1)
    )
    
    # Check log count threshold
    log_count_monitor = monitors.filter(metric_name='audit_log_count').first()
    if log_count_monitor and log_count_monitor.metric_value > AUDIT_LOG_COUNT_THRESHOLD:
        alerts.append({
            'metric': 'audit_log_count',
            'value': log_count_monitor.metric_value,
            'threshold': AUDIT_LOG_COUNT_THRESHOLD,
            'severity': 'warning',
            'message': f'High audit log count detected: {log_count_monitor.metric_value}'
        })
    
    # Check error rate threshold
    error_rate_monitor = monitors.filter(metric_name='audit_error_rate').first()
    if error_rate_monitor and error_rate_monitor.metric_value > AUDIT_ERROR_RATE_THRESHOLD:
        alerts.append({
            'metric': 'audit_error_rate',
            'value': error_rate_monitor.metric_value,
            'threshold': AUDIT_ERROR_RATE_THRESHOLD,
            'severity': 'critical',
            'message': f'High audit error rate detected: {error_rate_monitor.metric_value:.2%}'
        })
    
    # Check response time threshold
    response_time_monitor = monitors.filter(metric_name='audit_response_time').first()
    if response_time_monitor and response_time_monitor.metric_value > AUDIT_RESPONSE_TIME_THRESHOLD:
        alerts.append({
            'metric': 'audit_response_time',
            'value': response_time_monitor.metric_value,
            'threshold': AUDIT_RESPONSE_TIME_THRESHOLD,
            'severity': 'warning',
            'message': f'High audit response time detected: {response_time_monitor.metric_value}ms'
        })
    
    return alerts

def get_audit_monitoring_dashboard_data(organization, organization_context):
    """
    Get data for the audit monitoring dashboard.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        dict: Dashboard data including current metrics and trends
    """
    # Get current metrics
    current_metrics = {}
    for metric_name in ['audit_log_count', 'audit_error_rate', 'audit_response_time']:
        monitor = OrganizationMonitor.objects.filter(
            organization=organization,
            organization_context=organization_context,
            metric_name=metric_name
        ).order_by('-timestamp').first()
        
        if monitor:
            current_metrics[metric_name] = monitor.metric_value
    
    # Get trends (last 7 days)
    trends = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        day_metrics = {}
        
        for metric_name in ['audit_log_count', 'audit_error_rate', 'audit_response_time']:
            monitor = OrganizationMonitor.objects.filter(
                organization=organization,
                organization_context=organization_context,
                metric_name=metric_name,
                timestamp__date=date.date()
            ).first()
            
            if monitor:
                day_metrics[metric_name] = monitor.metric_value
        
        if day_metrics:
            trends.append({
                'date': date.date(),
                'metrics': day_metrics
            })
    
    return {
        'current_metrics': current_metrics,
        'trends': trends
    }

def generate_audit_monitoring_report(organization, organization_context, report_type='daily'):
    """
    Generate an audit monitoring report.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        report_type: Type of report ('daily', 'weekly', 'monthly')
        
    Returns:
        dict: Generated report data
    """
    # Determine date range based on report type
    if report_type == 'daily':
        start_date = timezone.now() - timedelta(days=1)
    elif report_type == 'weekly':
        start_date = timezone.now() - timedelta(weeks=1)
    else:  # monthly
        start_date = timezone.now() - timedelta(days=30)
    
    # Get metrics for the period
    metrics = {}
    for metric_name in ['audit_log_count', 'audit_error_rate', 'audit_response_time']:
        monitors = OrganizationMonitor.objects.filter(
            organization=organization,
            organization_context=organization_context,
            metric_name=metric_name,
            timestamp__gte=start_date
        )
        
        if monitors.exists():
            metrics[metric_name] = {
                'current': monitors.latest('timestamp').metric_value,
                'average': monitors.aggregate(Avg('metric_value'))['metric_value__avg'],
                'min': monitors.aggregate(Min('metric_value'))['metric_value__min'],
                'max': monitors.aggregate(Max('metric_value'))['metric_value__max']
            }
    
    # Generate alerts for the period
    alerts = generate_audit_alerts(organization, organization_context)
    
    # Generate recommendations based on metrics
    recommendations = []
    if metrics.get('audit_error_rate', {}).get('current', 0) > AUDIT_ERROR_RATE_THRESHOLD:
        recommendations.append('Investigate high error rate in audit logs')
    if metrics.get('audit_response_time', {}).get('current', 0) > AUDIT_RESPONSE_TIME_THRESHOLD:
        recommendations.append('Optimize audit logging performance')
    
    # Calculate statistics
    statistics = {
        'total_audits': Audit.objects.filter(
            organization=organization,
            timestamp__gte=start_date
        ).count(),
        'error_count': Audit.objects.filter(
            organization=organization,
            status='failed',
            timestamp__gte=start_date
        ).count(),
        'avg_response_time': metrics.get('audit_response_time', {}).get('average', 0)
    }
    
    return {
        'metrics': metrics,
        'alerts': alerts,
        'recommendations': recommendations,
        'statistics': statistics
    }

def monitor_audit_system(organization, organization_context):
    """
    Run the complete audit monitoring system.
    
    Args:
        organization: The organization to monitor
        organization_context: The organization context
        
    Returns:
        dict: Monitoring results
    """
    # Run individual monitors
    log_count = monitor_audit_log_count(organization, organization_context)
    error_rate = monitor_audit_error_rate(organization, organization_context)
    response_time = monitor_audit_response_time(organization, organization_context)
    
    # Generate alerts
    alerts = generate_audit_alerts(organization, organization_context)
    
    # Get dashboard data
    dashboard_data = get_audit_monitoring_dashboard_data(organization, organization_context)
    
    return {
        'log_count': log_count.metric_value if log_count else 0,
        'error_rate': error_rate.metric_value if error_rate else 0,
        'response_time': response_time.metric_value if response_time else 0,
        'alerts': alerts,
        'dashboard_data': dashboard_data
    } 