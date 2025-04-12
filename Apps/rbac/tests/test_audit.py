import pytest
from django.utils import timezone
from datetime import timedelta
from Apps.rbac.models import Audit, Role, Permission, UserRole, Resource, ResourceAccess
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def audit(organization, user):
    """Create a test audit entry"""
    return Audit.objects.create(
        organization=organization,
        user=user,
        action='test_action',
        resource_type='test_resource',
        resource_id=1,
        details={'test': 'data'},
        status='success'
    )

@pytest.fixture
def multiple_audits(organization, user, role, permission):
    """Create multiple test audit entries for testing compliance reporting"""
    audits = []
    
    # Create audit entries for role changes
    audits.append(Audit.objects.create(
        organization=organization,
        user=user,
        action='role_created',
        resource_type='role',
        resource_id=role.id,
        details={'role_name': role.name},
        status='success',
        timestamp=timezone.now() - timedelta(days=5)
    ))
    
    audits.append(Audit.objects.create(
        organization=organization,
        user=user,
        action='role_updated',
        resource_type='role',
        resource_id=role.id,
        details={'role_name': role.name, 'changes': {'name': 'Updated Role'}},
        status='success',
        timestamp=timezone.now() - timedelta(days=4)
    ))
    
    # Create audit entries for permission changes
    audits.append(Audit.objects.create(
        organization=organization,
        user=user,
        action='permission_created',
        resource_type='permission',
        resource_id=permission.id,
        details={'permission_name': permission.name},
        status='success',
        timestamp=timezone.now() - timedelta(days=3)
    ))
    
    # Create audit entries for user role assignments
    user_role = UserRole.objects.create(
        user=user,
        role=role,
        organization=organization,
        assigned_by=user
    )
    
    audits.append(Audit.objects.create(
        organization=organization,
        user=user,
        action='user_role_assigned',
        resource_type='user_role',
        resource_id=user_role.id,
        details={'user_id': user.id, 'role_id': role.id},
        status='success',
        timestamp=timezone.now() - timedelta(days=2)
    ))
    
    # Create audit entries for resource access
    resource = Resource.objects.create(
        name='Test Resource',
        resource_type='test',
        organization=organization,
        owner=user
    )
    
    resource_access = ResourceAccess.objects.create(
        resource=resource,
        user=user,
        access_type='read',
        organization=organization
    )
    
    audits.append(Audit.objects.create(
        organization=organization,
        user=user,
        action='resource_access_granted',
        resource_type='resource_access',
        resource_id=resource_access.id,
        details={'resource_id': resource.id, 'access_type': 'read'},
        status='success',
        timestamp=timezone.now() - timedelta(days=1)
    ))
    
    return audits

@pytest.mark.django_db
class TestAuditModel:
    """Test cases for the Audit model"""
    
    def test_audit_creation(self, audit):
        """Test that an audit entry can be created"""
        assert audit.id is not None
        assert audit.organization is not None
        assert audit.user is not None
        assert audit.action == 'test_action'
        assert audit.resource_type == 'test_resource'
        assert audit.resource_id == 1
        assert audit.details == {'test': 'data'}
        assert audit.status == 'success'
        assert audit.timestamp is not None
    
    def test_audit_str(self, audit):
        """Test the string representation of an audit entry"""
        expected_str = f"Audit: {audit.action} on {audit.resource_type} {audit.resource_id}"
        assert str(audit) == expected_str
    
    def test_audit_clean(self, audit):
        """Test the clean method of the audit model"""
        audit.clean()  # Should not raise any exceptions
    
    def test_audit_organization_isolation(self, audit, test_organization):
        """Test that audit entries are isolated by organization"""
        # Try to access the audit from a different organization
        with pytest.raises(Audit.DoesNotExist):
            Audit.objects.filter(organization=test_organization).get(id=audit.id)

@pytest.mark.django_db
class TestComplianceReporting:
    """Test cases for compliance reporting"""
    
    def test_generate_role_changes_report(self, multiple_audits, organization):
        """Test generating a report of role changes"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='role_changes',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'role_changes' in report
        assert len(report['role_changes']) == 2  # Two role-related audit entries
    
    def test_generate_permission_changes_report(self, multiple_audits, organization):
        """Test generating a report of permission changes"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='permission_changes',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'permission_changes' in report
        assert len(report['permission_changes']) == 1  # One permission-related audit entry
    
    def test_generate_user_role_assignments_report(self, multiple_audits, organization):
        """Test generating a report of user role assignments"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='user_role_assignments',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'user_role_assignments' in report
        assert len(report['user_role_assignments']) == 1  # One user role assignment audit entry
    
    def test_generate_resource_access_report(self, multiple_audits, organization):
        """Test generating a report of resource access changes"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='resource_access',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'resource_access' in report
        assert len(report['resource_access']) == 1  # One resource access audit entry
    
    def test_generate_comprehensive_report(self, multiple_audits, organization):
        """Test generating a comprehensive compliance report"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='comprehensive',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'role_changes' in report
        assert 'permission_changes' in report
        assert 'user_role_assignments' in report
        assert 'resource_access' in report
        assert len(report['role_changes']) == 2
        assert len(report['permission_changes']) == 1
        assert len(report['user_role_assignments']) == 1
        assert len(report['resource_access']) == 1
    
    def test_generate_report_with_date_filter(self, multiple_audits, organization):
        """Test generating a report with date filtering"""
        # Generate a report for the last 3 days
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='comprehensive',
            start_date=timezone.now() - timedelta(days=3),
            end_date=timezone.now()
        )
        
        assert report is not None
        # Should only include audit entries from the last 3 days
        assert len(report['role_changes']) == 0  # No role-related audit entries from the last 3 days
        assert len(report['permission_changes']) == 0  # No permission-related audit entries from the last 3 days
        assert len(report['user_role_assignments']) == 1
        assert len(report['resource_access']) == 1
    
    def test_generate_report_with_invalid_type(self, multiple_audits, organization):
        """Test generating a report with an invalid report type"""
        with pytest.raises(ValueError):
            Audit.generate_compliance_report(
                organization=organization,
                report_type='invalid_type',
                start_date=timezone.now() - timedelta(days=10),
                end_date=timezone.now()
            )
    
    def test_generate_report_with_invalid_date_range(self, multiple_audits, organization):
        """Test generating a report with an invalid date range"""
        with pytest.raises(ValueError):
            Audit.generate_compliance_report(
                organization=organization,
                report_type='comprehensive',
                start_date=timezone.now(),
                end_date=timezone.now() - timedelta(days=10)  # End date before start date
            )
    
    def test_generate_report_with_no_data(self, organization):
        """Test generating a report when there is no audit data"""
        report = Audit.generate_compliance_report(
            organization=organization,
            report_type='comprehensive',
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now()
        )
        
        assert report is not None
        assert 'role_changes' in report
        assert 'permission_changes' in report
        assert 'user_role_assignments' in report
        assert 'resource_access' in report
        assert len(report['role_changes']) == 0
        assert len(report['permission_changes']) == 0
        assert len(report['user_role_assignments']) == 0
        assert len(report['resource_access']) == 0

@pytest.mark.django_db
class TestAuditRetention:
    """Test cases for audit retention functionality"""
    
    def test_audit_retention_period_default(self, audit):
        """Test that the default retention period is set correctly"""
        assert audit.retention_period == 365  # Default 1 year retention
        
    def test_audit_retention_period_custom(self, organization, user):
        """Test that a custom retention period can be set"""
        custom_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='test_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            retention_period=180  # 6 months retention
        )
        assert custom_audit.retention_period == 180
        
    def test_cleanup_expired_audits(self, organization, user):
        """Test that expired audit logs are cleaned up"""
        # Create an audit log that has expired (older than retention period)
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
        deleted_count = Audit.cleanup_expired_audits(organization)
        
        # Check that the expired audit was deleted
        assert deleted_count == 1
        with pytest.raises(Audit.DoesNotExist):
            Audit.objects.get(id=expired_audit.id)
        
        # Check that the valid audit was not deleted
        assert Audit.objects.filter(id=valid_audit.id).exists()
        
    def test_cleanup_expired_audits_with_custom_retention(self, organization, user):
        """Test that expired audit logs with custom retention periods are cleaned up"""
        # Create an audit log with a custom retention period that has expired
        custom_expired_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='custom_expired_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=200),  # Older than custom retention
            retention_period=180  # 6 months retention
        )
        
        # Create an audit log with default retention that has not expired
        default_valid_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='default_valid_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=100),  # Within default retention
            retention_period=365  # Default retention
        )
        
        # Run the cleanup
        deleted_count = Audit.cleanup_expired_audits(organization)
        
        # Check that the custom expired audit was deleted
        assert deleted_count == 1
        with pytest.raises(Audit.DoesNotExist):
            Audit.objects.get(id=custom_expired_audit.id)
        
        # Check that the default valid audit was not deleted
        assert Audit.objects.filter(id=default_valid_audit.id).exists()
        
    def test_cleanup_expired_audits_with_no_expired(self, organization, user):
        """Test that no audits are deleted if none have expired"""
        # Create audit logs that have not expired
        for i in range(5):
            Audit.objects.create(
                organization=organization,
                user=user,
                action=f'valid_action_{i}',
                resource_type='test_resource',
                resource_id=i,
                details={'test': 'data'},
                status='success',
                timestamp=timezone.now() - timedelta(days=100),  # Within retention period
                retention_period=365
            )
        
        # Run the cleanup
        deleted_count = Audit.cleanup_expired_audits(organization)
        
        # Check that no audits were deleted
        assert deleted_count == 0
        assert Audit.objects.filter(organization=organization).count() == 5
        
    def test_cleanup_expired_audits_with_organization_isolation(self, organization, test_organization, user):
        """Test that audit cleanup respects organization isolation"""
        # Create an expired audit for the main organization
        expired_audit = Audit.objects.create(
            organization=organization,
            user=user,
            action='expired_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=400),  # Older than retention period
            retention_period=365
        )
        
        # Create an expired audit for the test organization
        test_expired_audit = Audit.objects.create(
            organization=test_organization,
            user=user,
            action='test_expired_action',
            resource_type='test_resource',
            resource_id=1,
            details={'test': 'data'},
            status='success',
            timestamp=timezone.now() - timedelta(days=400),  # Older than retention period
            retention_period=365
        )
        
        # Run the cleanup for the main organization
        deleted_count = Audit.cleanup_expired_audits(organization)
        
        # Check that only the expired audit for the main organization was deleted
        assert deleted_count == 1
        with pytest.raises(Audit.DoesNotExist):
            Audit.objects.get(id=expired_audit.id)
        
        # Check that the expired audit for the test organization was not deleted
        assert Audit.objects.filter(id=test_expired_audit.id).exists()
        
    def test_cleanup_expired_audits_with_bulk_operation(self, organization, user):
        """Test that bulk cleanup of expired audits works correctly"""
        # Create multiple expired audit logs
        expired_audits = []
        for i in range(10):
            expired_audits.append(Audit.objects.create(
                organization=organization,
                user=user,
                action=f'expired_action_{i}',
                resource_type='test_resource',
                resource_id=i,
                details={'test': 'data'},
                status='success',
                timestamp=timezone.now() - timedelta(days=400),  # Older than retention period
                retention_period=365
            ))
        
        # Create multiple valid audit logs
        valid_audits = []
        for i in range(5):
            valid_audits.append(Audit.objects.create(
                organization=organization,
                user=user,
                action=f'valid_action_{i}',
                resource_type='test_resource',
                resource_id=i+10,
                details={'test': 'data'},
                status='success',
                timestamp=timezone.now() - timedelta(days=100),  # Within retention period
                retention_period=365
            ))
        
        # Run the cleanup
        deleted_count = Audit.cleanup_expired_audits(organization)
        
        # Check that all expired audits were deleted
        assert deleted_count == 10
        for audit in expired_audits:
            with pytest.raises(Audit.DoesNotExist):
                Audit.objects.get(id=audit.id)
        
        # Check that all valid audits were not deleted
        for audit in valid_audits:
            assert Audit.objects.filter(id=audit.id).exists() 