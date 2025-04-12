import pytest
from django.utils import timezone
from datetime import timedelta
from Apps.rbac.models import Audit, OrganizationMonitor, OrganizationContext
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def organization_context(organization):
    """Create a test organization context"""
    return OrganizationContext.objects.create(
        organization=organization,
        name='Test Context',
        description='Test organization context'
    )

@pytest.fixture
def audit_monitor(organization, organization_context):
    """Create a test audit monitor"""
    return OrganizationMonitor.objects.create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_log_count',
        metric_value=100,
        metric_type='counter',
        is_active=True
    )

@pytest.fixture
def multiple_audit_monitors(organization, organization_context):
    """Create multiple test audit monitors for different metrics"""
    monitors = []
    
    # Create monitors for different audit metrics
    monitors.append(OrganizationMonitor.objects.create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_log_count',
        metric_value=150,
        metric_type='counter',
        timestamp=timezone.now() - timedelta(days=5)
    ))
    
    monitors.append(OrganizationMonitor.objects.create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_error_rate',
        metric_value=0.15,
        metric_type='gauge',
        timestamp=timezone.now() - timedelta(days=5)
    ))
    
    monitors.append(OrganizationMonitor.objects.create(
        organization=organization,
        organization_context=organization_context,
        metric_name='audit_response_time',
        metric_value=600,
        metric_type='histogram',
        timestamp=timezone.now() - timedelta(days=5)
    ))
    
    return monitors

@pytest.fixture
def multiple_audits(organization):
    """Create multiple test audit logs"""
    audits = []
    
    # Create audit logs with different statuses
    for i in range(10):
        status = 'success' if i % 3 != 0 else 'failed'
        audits.append(Audit.objects.create(
            organization=organization,
            action='test_action',
            resource_type='test_resource',
            resource_id=i,
            user_id=1,
            status=status,
            timestamp=timezone.now() - timedelta(hours=i)
        ))
    
    return audits

@pytest.mark.django_db
class TestAuditMonitoring:
    """Test suite for Audit monitoring functionality"""
    
    def test_audit_log_count_monitoring(self, organization, organization_context, test_user):
        """Test monitoring of audit log count"""
        from Apps.rbac.operations.audit_monitoring import monitor_audit_log_count
        
        # Create test audit logs
        for i in range(5):
            Audit.objects.create(
                organization=organization,
                action='test_action',
                resource_type='test_resource',
                resource_id=i,
                user_id=test_user.id,
                status='success',
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # Monitor audit log count
        monitor = monitor_audit_log_count(organization, organization_context)
        
        assert monitor is not None
        assert monitor.metric_name == 'audit_log_count'
        assert monitor.metric_value == 5
        assert monitor.metric_type == 'counter'
    
    def test_audit_error_rate_monitoring(self, organization, organization_context, test_user):
        """Test monitoring of audit error rate"""
        from Apps.rbac.operations.audit_monitoring import monitor_audit_error_rate
        
        # Create test audit logs with different statuses
        for i in range(10):
            status = 'success' if i % 3 != 0 else 'failed'
            Audit.objects.create(
                organization=organization,
                action='test_action',
                resource_type='test_resource',
                resource_id=i,
                user_id=test_user.id,
                status=status,
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        # Monitor audit error rate
        monitor = monitor_audit_error_rate(organization, organization_context)
        
        assert monitor is not None
        assert monitor.metric_name == 'audit_error_rate'
        # The error rate should be 0.4 (4 failed out of 10 total)
        assert abs(monitor.metric_value - 0.4) < 0.01  # Allow for small floating point differences
        assert monitor.metric_type == 'gauge'
    
    def test_audit_response_time_monitoring(self, organization, organization_context, test_user):
        """Test monitoring of audit API response time"""
        from Apps.rbac.operations.audit_monitoring import monitor_audit_response_time
        
        # Create test audit logs with response times
        for i in range(5):
            Audit.objects.create(
                organization=organization,
                action='test_action',
                resource_type='test_resource',
                resource_id=i,
                user_id=test_user.id,
                status='success',
                timestamp=timezone.now() - timedelta(hours=i),
                details={'response_time': 200 + i * 100}  # Store as integer in JSON
            )
        
        # Monitor audit response time
        monitor = monitor_audit_response_time(organization, organization_context)
        
        assert monitor is not None
        assert monitor.metric_name == 'audit_response_time'
        assert abs(monitor.metric_value - 400) < 0.01  # Allow for small floating point differences
        assert monitor.metric_type == 'histogram'
    
    def test_audit_alert_generation(self, organization, organization_context, test_user):
        """Test generation of audit alerts"""
        from Apps.rbac.operations.audit_monitoring import generate_audit_alerts
        
        # Create monitors with values that should trigger alerts
        OrganizationMonitor.objects.create(
            organization=organization,
            organization_context=organization_context,
            metric_name='audit_log_count',
            metric_value=1500,  # Above threshold (1000)
            metric_type='counter',
            timestamp=timezone.now()
        )
        
        OrganizationMonitor.objects.create(
            organization=organization,
            organization_context=organization_context,
            metric_name='audit_error_rate',
            metric_value=0.15,  # Above threshold (0.1)
            metric_type='gauge',
            timestamp=timezone.now()
        )
        
        OrganizationMonitor.objects.create(
            organization=organization,
            organization_context=organization_context,
            metric_name='audit_response_time',
            metric_value=800,  # Above threshold (500)
            metric_type='histogram',
            timestamp=timezone.now()
        )
        
        # Generate alerts
        alerts = generate_audit_alerts(organization, organization_context)
        
        assert len(alerts) == 3
        # Verify each alert has the correct properties
        for alert in alerts:
            assert alert['severity'] in ['warning', 'critical']
            assert alert['metric'] in ['audit_log_count', 'audit_error_rate', 'audit_response_time']
            assert alert['value'] > alert['threshold']
    
    def test_audit_monitoring_dashboard_data(self, organization, organization_context, test_user):
        """Test generation of audit monitoring dashboard data"""
        from Apps.rbac.operations.audit_monitoring import get_audit_monitoring_dashboard_data
        
        # Create monitors for the last 7 days
        for i in range(7):
            OrganizationMonitor.objects.create(
                organization=organization,
                organization_context=organization_context,
                metric_name='audit_log_count',
                metric_value=50 + i * 10,
                metric_type='counter',
                timestamp=timezone.now() - timedelta(days=i)
            )
        
        # Get dashboard data
        dashboard_data = get_audit_monitoring_dashboard_data(organization, organization_context)
        
        assert 'current_metrics' in dashboard_data
        assert 'trends' in dashboard_data
        assert len(dashboard_data['trends']) == 7
    
    def test_audit_monitoring_report_generation(self, organization, organization_context, test_user):
        """Test generation of audit monitoring report"""
        from Apps.rbac.operations.audit_monitoring import generate_audit_monitoring_report
        
        # Create monitors for the last 30 days
        for i in range(30):
            OrganizationMonitor.objects.create(
                organization=organization,
                organization_context=organization_context,
                metric_name='audit_log_count',
                metric_value=50 + i * 5,
                metric_type='counter',
                timestamp=timezone.now() - timedelta(days=i)
            )
        
        # Generate report
        report = generate_audit_monitoring_report(organization, organization_context)
        
        assert 'metrics' in report
        assert 'alerts' in report
        assert 'recommendations' in report
        assert 'statistics' in report
        # The report contains metrics by name, not by count
        assert 'audit_log_count' in report['metrics']
    
    def test_audit_monitoring_integration(self, organization, organization_context, test_user):
        """Test integration of all audit monitoring components"""
        from Apps.rbac.operations.audit_monitoring import (
            monitor_audit_log_count,
            monitor_audit_error_rate,
            monitor_audit_response_time,
            generate_audit_alerts,
            get_audit_monitoring_dashboard_data,
            generate_audit_monitoring_report
        )
        
        # Create test audit logs
        for i in range(10):
            status = 'success' if i % 3 != 0 else 'failed'
            Audit.objects.create(
                organization=organization,
                action='test_action',
                resource_type='test_resource',
                resource_id=i,
                user_id=test_user.id,
                status=status,
                timestamp=timezone.now() - timedelta(hours=i),
                details={'response_time': 200 + i * 50}  # Store as integer in JSON
            )
        
        # Run all monitoring functions
        log_count_monitor = monitor_audit_log_count(organization, organization_context)
        error_rate_monitor = monitor_audit_error_rate(organization, organization_context)
        response_time_monitor = monitor_audit_response_time(organization, organization_context)
        alerts = generate_audit_alerts(organization, organization_context)
        dashboard_data = get_audit_monitoring_dashboard_data(organization, organization_context)
        report = generate_audit_monitoring_report(organization, organization_context)
        
        # Verify results
        assert log_count_monitor is not None
        assert error_rate_monitor is not None
        assert response_time_monitor is not None
        assert isinstance(alerts, list)
        assert isinstance(dashboard_data, dict)
        assert isinstance(report, dict) 