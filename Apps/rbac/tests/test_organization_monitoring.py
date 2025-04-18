import pytest
from django.utils import timezone
from Apps.rbac.models import OrganizationContext, OrganizationMonitor
from Apps.entity.models import Organization
from datetime import datetime, timedelta

@pytest.fixture
def organization_context(organization):
    """Create a test organization context"""
    return OrganizationContext.objects.create(
        organization=organization,
        name="Test Context",
        description="Test organization context"
    )

@pytest.fixture
def organization_monitor(organization_context):
    """Create a test organization monitor"""
    return OrganizationMonitor.objects.create(
        organization_context=organization_context,
        metric_name="test_metric",
        metric_value=100,
        metric_type="counter"
    )

@pytest.mark.django_db
class TestOrganizationMonitor:
    """Tests for the OrganizationMonitor model"""
    
    def test_create_organization_monitor(self, organization_context):
        """Test creating a basic organization monitor"""
        monitor = OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=100,
            metric_type="counter"
        )
        
        assert monitor.organization_context == organization_context
        assert monitor.metric_name == "test_metric"
        assert monitor.metric_value == 100
        assert monitor.metric_type == "counter"
        assert monitor.timestamp is not None
        assert monitor.is_active is True
    
    def test_organization_monitor_str(self, organization_monitor):
        """Test the string representation of an organization monitor"""
        expected_str = f"{organization_monitor.organization_context.name} - {organization_monitor.metric_name}: {organization_monitor.metric_value}"
        assert str(organization_monitor) == expected_str
    
    def test_organization_monitor_deactivation(self, organization_monitor):
        """Test deactivating an organization monitor"""
        organization_monitor.deactivate()
        assert organization_monitor.is_active is False
        assert organization_monitor.deactivated_at is not None
    
    def test_organization_monitor_activation(self, organization_monitor):
        """Test activating an organization monitor"""
        # First deactivate
        organization_monitor.deactivate()
        assert organization_monitor.is_active is False
        
        # Then activate
        organization_monitor.activate()
        assert organization_monitor.is_active is True
        assert organization_monitor.deactivated_at is None
    
    def test_organization_monitor_validation(self, organization_context):
        """Test organization monitor validation"""
        # Test with invalid metric type
        monitor = OrganizationMonitor(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=100,
            metric_type="invalid_type"
        )
        with pytest.raises(ValueError):
            monitor.full_clean()
    
    def test_organization_monitor_get_latest_metrics(self, organization_context):
        """Test getting latest metrics for an organization context"""
        # Create multiple monitors with different timestamps
        now = timezone.now()
        
        # Create a monitor from 1 hour ago
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=100,
            metric_type="counter",
            timestamp=now - timedelta(hours=1)
        )
        
        # Create a monitor from 30 minutes ago
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=200,
            metric_type="counter",
            timestamp=now - timedelta(minutes=30)
        )
        
        # Create a monitor from now
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=300,
            metric_type="counter",
            timestamp=now
        )
        
        # Get the latest metrics
        latest_metrics = OrganizationMonitor.get_latest_metrics(organization_context)
        
        # Check that we got the latest metric
        assert len(latest_metrics) == 1
        assert latest_metrics[0].metric_value == 300
    
    def test_organization_monitor_get_metrics_by_time_range(self, organization_context):
        """Test getting metrics for an organization context within a time range"""
        # Create a fixed reference time
        reference_time = timezone.now()
        
        # Create a monitor from 2 hours ago
        monitor1 = OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=100,
            metric_type="counter",
            timestamp=reference_time - timedelta(hours=2)
        )
        
        # Create a monitor from 1 hour ago
        monitor2 = OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=200,
            metric_type="counter",
            timestamp=reference_time - timedelta(hours=1)
        )
        
        # Create a monitor from 30 minutes ago
        monitor3 = OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=300,
            metric_type="counter",
            timestamp=reference_time - timedelta(minutes=30)
        )
        
        # Create a monitor from now
        monitor4 = OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=400,
            metric_type="counter",
            timestamp=reference_time
        )
        
        # Get metrics from 45 minutes ago to now (after Monitor 2's timestamp)
        start_time = reference_time - timedelta(minutes=45)
        end_time = reference_time
        
        metrics = OrganizationMonitor.get_metrics_by_time_range(
            organization_context,
            start_time,
            end_time
        )
        
        # Check that we got the metrics within the time range
        assert len(metrics) == 2
        assert metrics[0].metric_value == 300
        assert metrics[1].metric_value == 400
    
    def test_organization_monitor_get_metrics_by_type(self, organization_context):
        """Test getting metrics for an organization context by type"""
        # Create multiple monitors with different types
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="counter_metric",
            metric_value=100,
            metric_type="counter"
        )
        
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="gauge_metric",
            metric_value=200,
            metric_type="gauge"
        )
        
        # Get metrics by type
        counter_metrics = OrganizationMonitor.get_metrics_by_type(organization_context, "counter")
        gauge_metrics = OrganizationMonitor.get_metrics_by_type(organization_context, "gauge")
        
        # Check that we got the correct metrics
        assert len(counter_metrics) == 1
        assert counter_metrics[0].metric_value == 100
        assert len(gauge_metrics) == 1
        assert gauge_metrics[0].metric_value == 200
    
    def test_organization_monitor_get_metrics_by_name(self, organization_context):
        """Test getting metrics for an organization context by name"""
        # Create multiple monitors with different names
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="metric_1",
            metric_value=100,
            metric_type="counter"
        )
        
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="metric_2",
            metric_value=200,
            metric_type="counter"
        )
        
        # Get metrics by name
        metrics_1 = OrganizationMonitor.get_metrics_by_name(organization_context, "metric_1")
        metrics_2 = OrganizationMonitor.get_metrics_by_name(organization_context, "metric_2")
        
        # Check that we got the correct metrics
        assert len(metrics_1) == 1
        assert metrics_1[0].metric_value == 100
        assert len(metrics_2) == 1
        assert metrics_2[0].metric_value == 200
    
    def test_organization_monitor_aggregate_metrics(self, organization_context):
        """Test aggregating metrics for an organization context"""
        # Create multiple monitors with the same name
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=100,
            metric_type="counter"
        )
        
        OrganizationMonitor.objects.create(
            organization_context=organization_context,
            metric_name="test_metric",
            metric_value=200,
            metric_type="counter"
        )
        
        # Test different aggregation types
        sum_value = OrganizationMonitor.aggregate_metrics(organization_context, "test_metric", "sum")
        avg_value = OrganizationMonitor.aggregate_metrics(organization_context, "test_metric", "avg")
        min_value = OrganizationMonitor.aggregate_metrics(organization_context, "test_metric", "min")
        max_value = OrganizationMonitor.aggregate_metrics(organization_context, "test_metric", "max")
        
        # Check aggregation results
        assert sum_value == 300
        assert avg_value == 150
        assert min_value == 100
        assert max_value == 200 