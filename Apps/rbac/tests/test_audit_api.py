import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from Apps.rbac.models import Audit, Role, Permission, UserRole, Resource, ResourceAccess
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def audit_api_url():
    """Return the base URL for audit API endpoints"""
    return reverse('rbac:audit-list')

@pytest.fixture
def audit(organization, user):
    """Create a sample audit entry for testing"""
    return Audit.objects.create(
        organization=organization,
        user=user,
        action='test_action',
        resource_type='test_resource',
        resource_id=1,
        details={'test': 'data'},
        status='success',
        timestamp=timezone.now(),
        retention_period=365
    )

@pytest.fixture
def audit_detail_api_url(audit):
    """Return the URL for a specific audit entry"""
    return reverse('rbac:audit-detail', kwargs={'pk': audit.id})

@pytest.fixture
def compliance_report_api_url():
    """Return the URL for compliance report API endpoint"""
    return reverse('rbac:audit-compliance-report')

@pytest.fixture
def cleanup_audits_api_url():
    """Return the URL for cleanup audits API endpoint"""
    return reverse('rbac:audit-cleanup-expired')

@pytest.fixture
def auth_client(client, user):
    """Create an authenticated client for testing"""
    client.force_login(user)
    return client

@pytest.fixture
def multiple_audits(organization, user):
    """Create multiple audit entries for testing"""
    audits = []
    actions = ['role_created', 'permission_changed', 'user_role_assigned', 'resource_accessed']
    resource_types = ['role', 'permission', 'user_role', 'resource']
    
    for i in range(10):
        action = actions[i % len(actions)]
        resource_type = resource_types[i % len(resource_types)]
        audit = Audit.objects.create(
            organization=organization,
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=i+1,
            details={'test': f'data_{i}'},
            status='success',
            timestamp=timezone.now() - timedelta(days=i),
            retention_period=365
        )
        audits.append(audit)
    
    return audits

@pytest.mark.django_db
class TestAuditAPI:
    """Test cases for Audit API endpoints"""
    
    def test_list_audits(self, client, auth_client, audit_api_url, audit, multiple_audits):
        """Test retrieving a list of audit logs"""
        response = auth_client.get(audit_api_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert len(response.json()['data']) > 0
    
    def test_retrieve_audit(self, client, auth_client, audit_detail_api_url, audit):
        """Test retrieving a specific audit log"""
        response = auth_client.get(audit_detail_api_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['data']['id'] == str(audit.id)
    
    def test_filter_audits_by_resource_type(self, client, auth_client, audit_api_url, multiple_audits):
        """Test filtering audit logs by resource type"""
        response = auth_client.get(f"{audit_api_url}?resource_type=role")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert all(item['attributes']['resource_type'] == 'role' for item in response.json()['data'])
    
    def test_filter_audits_by_action(self, client, auth_client, audit_api_url, multiple_audits):
        """Test filtering audit logs by action"""
        response = auth_client.get(f"{audit_api_url}?action=role_created")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert all(item['attributes']['action'] == 'role_created' for item in response.json()['data'])
    
    def test_filter_audits_by_date_range(self, client, auth_client, audit_api_url, multiple_audits):
        """Test filtering audit logs by date range"""
        start_date = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        response = auth_client.get(f"{audit_api_url}?start_date={start_date}&end_date={end_date}")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
    
    def test_filter_audits_by_user(self, client, auth_client, audit_api_url, multiple_audits, user):
        """Test filtering audit logs by user"""
        response = auth_client.get(f"{audit_api_url}?user={user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert all(item['attributes']['user'] == user.id for item in response.json()['data'])
    
    def test_filter_audits_by_status(self, client, auth_client, audit_api_url, multiple_audits):
        """Test filtering audit logs by status"""
        response = auth_client.get(f"{audit_api_url}?status=success")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert all(item['attributes']['status'] == 'success' for item in response.json()['data'])
    
    def test_generate_compliance_report_role_changes(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a compliance report for role changes"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=role_changes")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'role_changes' in response.json()['data']['attributes']
    
    def test_generate_compliance_report_permission_changes(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a compliance report for permission changes"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=permission_changes")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'permission_changes' in response.json()['data']['attributes']
    
    def test_generate_compliance_report_user_role_assignments(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a compliance report for user role assignments"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=user_role_assignments")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'user_role_assignments' in response.json()['data']['attributes']
    
    def test_generate_compliance_report_resource_access(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a compliance report for resource access"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=resource_access")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'resource_access' in response.json()['data']['attributes']
    
    def test_generate_compliance_report_comprehensive(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a comprehensive compliance report"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=comprehensive")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'role_changes' in response.json()['data']['attributes']
        assert 'permission_changes' in response.json()['data']['attributes']
        assert 'user_role_assignments' in response.json()['data']['attributes']
        assert 'resource_access' in response.json()['data']['attributes']
    
    def test_generate_compliance_report_with_date_range(self, client, auth_client, compliance_report_api_url, multiple_audits):
        """Test generating a compliance report with date range"""
        start_date = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = timezone.now().strftime('%Y-%m-%d')
        response = auth_client.get(f"{compliance_report_api_url}?report_type=comprehensive&start_date={start_date}&end_date={end_date}")
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
    
    def test_generate_compliance_report_invalid_type(self, client, auth_client, compliance_report_api_url):
        """Test generating a compliance report with invalid report type"""
        response = auth_client.get(f"{compliance_report_api_url}?report_type=invalid_type")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_generate_compliance_report_invalid_date_range(self, client, auth_client, compliance_report_api_url):
        """Test generating a compliance report with invalid date range"""
        start_date = timezone.now().strftime('%Y-%m-%d')
        end_date = (timezone.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        response = auth_client.get(f"{compliance_report_api_url}?report_type=comprehensive&start_date={start_date}&end_date={end_date}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cleanup_expired_audits(self, client, auth_client, cleanup_audits_api_url, organization, user):
        """Test cleaning up expired audit logs"""
        # Create an audit log that has expired
        expired_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='expired_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=400),  # Older than default retention
            retention_period=365
        )
        
        # Create an audit log that has not expired
        valid_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='valid_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=100),  # Within retention period
            retention_period=365
        )
        
        # Run the cleanup
        response = auth_client.post(cleanup_audits_api_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['data']['attributes']['deleted_count'] == 1
        
        # Check that the expired audit was deleted
        with pytest.raises(Audit.DoesNotExist):
            Audit.objects.get(id=expired_audit.id)
        
        # Check that the valid audit was not deleted
        assert Audit.objects.filter(id=valid_audit.id).exists()
    
    def test_unauthorized_access(self, client, audit_api_url, audit_detail_api_url, compliance_report_api_url, cleanup_audits_api_url):
        """Test unauthorized access to audit API endpoints"""
        # Test list endpoint
        response = client.get(audit_api_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test detail endpoint
        response = client.get(audit_detail_api_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test compliance report endpoint
        response = client.get(compliance_report_api_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test cleanup endpoint
        response = client.post(cleanup_audits_api_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 