import pytest
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from Apps.rbac.models import OrganizationContext, Role, Permission, UserRole, Resource, ResourceAccess
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

@pytest.fixture
def organization1():
    """Create a test organization"""
    return Organization.objects.create(
        name="Organization 1",
        description="Test organization 1"
    )

@pytest.fixture
def organization2():
    """Create another test organization"""
    return Organization.objects.create(
        name="Organization 2",
        description="Test organization 2"
    )

@pytest.fixture
def user1(organization1):
    """Create a user in organization 1"""
    # Create a department for the organization
    department = Department.objects.create(
        name='Test Department',
        organization=organization1
    )
    
    # Create a team in the department
    team = Team.objects.create(
        name='Test Team',
        department=department
    )
    
    # Create the user
    user = User.objects.create_user(
        username='user1',
        email='user1@example.com',
        password='testpass123'
    )
    
    # Create a team membership to associate the user with the organization
    TeamMember.objects.create(
        team=team,
        user=user,
        role=TeamMember.Role.MEMBER,
        is_active=True
    )
    
    return user

@pytest.fixture
def user2(organization2):
    """Create a user in organization 2"""
    # Create a department for the organization
    department = Department.objects.create(
        name='Test Department',
        organization=organization2
    )
    
    # Create a team in the department
    team = Team.objects.create(
        name='Test Team',
        department=department
    )
    
    # Create the user
    user = User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='testpass123'
    )
    
    # Create a team membership to associate the user with the organization
    TeamMember.objects.create(
        team=team,
        user=user,
        role=TeamMember.Role.MEMBER,
        is_active=True
    )
    
    return user

@pytest.fixture
def role1(organization1):
    """Create a role in organization 1"""
    return Role.objects.create(
        name="Role 1",
        organization=organization1
    )

@pytest.fixture
def role2(organization2):
    """Create a role in organization 2"""
    return Role.objects.create(
        name="Role 2",
        organization=organization2
    )

@pytest.fixture
def permission1(organization1):
    """Create a permission in organization 1"""
    return Permission.objects.create(
        name="Permission 1",
        code="permission1",
        organization=organization1
    )

@pytest.fixture
def permission2(organization2):
    """Create a permission in organization 2"""
    return Permission.objects.create(
        name="Permission 2",
        code="permission2",
        organization=organization2
    )

@pytest.fixture
def user_role1(organization1, user1, role1):
    """Create a user role in organization 1"""
    return UserRole.objects.create(
        user=user1,
        role=role1,
        organization=organization1,
        assigned_by=user1
    )

@pytest.fixture
def user_role2(organization2, user2, role2):
    """Create a user role in organization 2"""
    return UserRole.objects.create(
        user=user2,
        role=role2,
        organization=organization2,
        assigned_by=user2
    )

@pytest.fixture
def resource1(organization1):
    """Create a resource in organization 1"""
    return Resource.objects.create(
        name="Resource 1",
        resource_type="test",
        organization=organization1
    )

@pytest.fixture
def resource2(organization2):
    """Create a resource in organization 2"""
    return Resource.objects.create(
        name="Resource 2",
        resource_type="test",
        organization=organization2
    )

@pytest.fixture
def cross_org_permission(organization1):
    """Create a cross-organization permission in organization 1"""
    return Permission.objects.create(
        name="Cross Organization Access",
        code="cross_org_access",
        organization=organization1
    )

@pytest.fixture
def cross_org_role(organization1, cross_org_permission):
    """Create a cross-organization role in organization 1"""
    role = Role.objects.create(
        name="Cross Organization Role",
        organization=organization1
    )
    role.permissions.add(cross_org_permission)
    return role

@pytest.fixture
def cross_org_user_role(organization1, user1, cross_org_role):
    """Create a cross-organization user role in organization 1"""
    return UserRole.objects.create(
        user=user1,
        role=cross_org_role,
        organization=organization1,
        assigned_by=user1
    )

@pytest.mark.django_db
class TestCrossOrganizationAccess:
    """Tests for cross-organization access functionality"""
    
    def test_cross_organization_permission_creation(self, organization1, cross_org_permission):
        """Test creating a cross-organization permission"""
        assert cross_org_permission.name == "Cross Organization Access"
        assert cross_org_permission.code == "cross_org_access"
        assert cross_org_permission.organization == organization1
    
    def test_cross_organization_role_creation(self, organization1, cross_org_role, cross_org_permission):
        """Test creating a cross-organization role"""
        assert cross_org_role.name == "Cross Organization Role"
        assert cross_org_role.organization == organization1
        assert cross_org_permission in cross_org_role.permissions.all()
    
    def test_cross_organization_user_role_creation(self, organization1, user1, cross_org_role, cross_org_user_role):
        """Test creating a cross-organization user role"""
        assert cross_org_user_role.user == user1
        assert cross_org_user_role.role == cross_org_role
        assert cross_org_user_role.organization == organization1
    
    def test_cross_organization_resource_access(self, organization1, organization2, user1, cross_org_user_role, resource2):
        """Test accessing a resource from another organization with cross-organization permission"""
        # Grant access to the resource
        resource2.grant_access(user1, "read")
        
        # Check if the user has access to the resource
        assert resource2.has_access(user1, "read") is True
        
        # Verify the access was created
        access = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access is not None
        assert access.is_active is True
    
    def test_cross_organization_resource_access_without_permission(self, organization1, organization2, user1, resource2):
        """Test accessing a resource from another organization without cross-organization permission"""
        # Try to grant access to the resource
        with pytest.raises(PermissionDenied):
            resource2.grant_access(user1, "read")
        
        # Check if the user has access to the resource
        assert resource2.has_access(user1, "read") is False
        
        # Verify no access was created
        access = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access is None
    
    def test_cross_organization_resource_access_revocation(self, organization1, organization2, user1, cross_org_user_role, resource2):
        """Test revoking access to a resource from another organization"""
        # Grant access to the resource
        resource2.grant_access(user1, "read")
        
        # Check if the user has access to the resource
        assert resource2.has_access(user1, "read") is True
        
        # Revoke access to the resource
        resource2.revoke_access(user1, "read")
        
        # Check if the user no longer has access to the resource
        assert resource2.has_access(user1, "read") is False
        
        # Verify the access was deactivated
        access = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access is not None
        assert access.is_active is False
    
    def test_cross_organization_resource_access_multiple_types(self, organization1, organization2, user1, cross_org_user_role, resource2):
        """Test accessing a resource from another organization with multiple access types"""
        # Grant different types of access to the resource
        resource2.grant_access(user1, "read")
        resource2.grant_access(user1, "write")
        
        # Check if the user has access to the resource with different types
        assert resource2.has_access(user1, "read") is True
        assert resource2.has_access(user1, "write") is True
        
        # Verify the accesses were created
        read_access = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        write_access = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="write",
            organization=organization2
        ).first()
        
        assert read_access is not None
        assert write_access is not None
        assert read_access.is_active is True
        assert write_access.is_active is True
    
    def test_cross_organization_resource_access_multiple_resources(self, organization1, organization2, user1, cross_org_user_role, resource1, resource2):
        """Test accessing multiple resources from different organizations"""
        # Grant access to resources from both organizations
        resource1.grant_access(user1, "read")
        resource2.grant_access(user1, "read")
        
        # Check if the user has access to both resources
        assert resource1.has_access(user1, "read") is True
        assert resource2.has_access(user1, "read") is True
        
        # Verify the accesses were created
        access1 = ResourceAccess.objects.filter(
            resource=resource1,
            user=user1,
            access_type="read",
            organization=organization1
        ).first()
        
        access2 = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access1 is not None
        assert access2 is not None
        assert access1.is_active is True
        assert access2.is_active is True
    
    def test_cross_organization_resource_access_multiple_users(self, organization1, organization2, user1, user2, cross_org_user_role, resource2):
        """Test multiple users accessing a resource from another organization"""
        # Grant access to the resource for both users
        resource2.grant_access(user1, "read")
        resource2.grant_access(user2, "read")
        
        # Check if both users have access to the resource
        assert resource2.has_access(user1, "read") is True
        assert resource2.has_access(user2, "read") is True
        
        # Verify the accesses were created
        access1 = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        access2 = ResourceAccess.objects.filter(
            resource=resource2,
            user=user2,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access1 is not None
        assert access2 is not None
        assert access1.is_active is True
        assert access2.is_active is True
    
    def test_cross_organization_resource_access_delegation(self, organization1, organization2, user1, user2, cross_org_user_role, resource2):
        """Test delegating access to a resource from another organization"""
        # Grant access to the resource for user1
        resource2.grant_access(user1, "read")
        
        # Create a delegated user role for user2
        delegated_role = UserRole.objects.create(
            user=user2,
            role=cross_org_user_role.role,
            organization=organization1,
            assigned_by=user1,
            delegated_by=cross_org_user_role,
            is_delegated=True
        )
        
        # Grant access to the resource for user2
        resource2.grant_access(user2, "read")
        
        # Check if both users have access to the resource
        assert resource2.has_access(user1, "read") is True
        assert resource2.has_access(user2, "read") is True
        
        # Verify the accesses were created
        access1 = ResourceAccess.objects.filter(
            resource=resource2,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        access2 = ResourceAccess.objects.filter(
            resource=resource2,
            user=user2,
            access_type="read",
            organization=organization2
        ).first()
        
        assert access1 is not None
        assert access2 is not None
        assert access1.is_active is True
        assert access2.is_active is True
        
        # Verify the delegated role was created
        assert delegated_role.is_delegated is True
        assert delegated_role.delegated_by == cross_org_user_role
    
    def test_cross_organization_resource_access_inheritance(self, organization1, organization2, user1, cross_org_user_role, resource1, resource2):
        """Test resource access inheritance across organizations"""
        # Create a parent resource in organization 1
        parent_resource = Resource.objects.create(
            name="Parent Resource",
            resource_type="test",
            organization=organization1,
            parent=resource1
        )
        
        # Create a child resource in organization 2
        child_resource = Resource.objects.create(
            name="Child Resource",
            resource_type="test",
            organization=organization2,
            parent=resource2
        )
        
        # Grant access to the parent resource
        parent_resource.grant_access(user1, "read")
        
        # Check if the user has access to the parent resource
        assert parent_resource.has_access(user1, "read") is True
        
        # Grant access to the child resource
        child_resource.grant_access(user1, "read")
        
        # Check if the user has access to the child resource
        assert child_resource.has_access(user1, "read") is True
        
        # Verify the accesses were created
        parent_access = ResourceAccess.objects.filter(
            resource=parent_resource,
            user=user1,
            access_type="read",
            organization=organization1
        ).first()
        
        child_access = ResourceAccess.objects.filter(
            resource=child_resource,
            user=user1,
            access_type="read",
            organization=organization2
        ).first()
        
        assert parent_access is not None
        assert child_access is not None
        assert parent_access.is_active is True
        assert child_access.is_active is True 