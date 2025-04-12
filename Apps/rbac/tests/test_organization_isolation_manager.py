import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import Role, Permission, UserRole, Resource, ResourceAccess, OrganizationContext
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def organization1():
    """Create a test organization"""
    return Organization.objects.create(
        name="Test Organization 1",
        description="Test organization 1"
    )

@pytest.fixture
def organization2():
    """Create another test organization"""
    return Organization.objects.create(
        name="Test Organization 2",
        description="Test organization 2"
    )

@pytest.fixture
def user1(organization1):
    """Create a test user for organization 1"""
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
        username='testuser1',
        email='test1@example.com',
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
    """Create a test user for organization 2"""
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
        username='testuser2',
        email='test2@example.com',
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
    """Create a test role for organization 1"""
    return Role.objects.create(
        name="Test Role 1",
        description="Test role 1",
        organization=organization1
    )

@pytest.fixture
def role2(organization2):
    """Create a test role for organization 2"""
    return Role.objects.create(
        name="Test Role 2",
        description="Test role 2",
        organization=organization2
    )

@pytest.fixture
def permission1(organization1):
    """Create a test permission for organization 1"""
    return Permission.objects.create(
        name="Test Permission 1",
        code="test_permission_1",
        description="Test permission 1",
        organization=organization1
    )

@pytest.fixture
def permission2(organization2):
    """Create a test permission for organization 2"""
    return Permission.objects.create(
        name="Test Permission 2",
        code="test_permission_2",
        description="Test permission 2",
        organization=organization2
    )

@pytest.fixture
def user_role1(user1, role1, organization1):
    """Create a test user role for organization 1"""
    return UserRole.objects.create(
        user=user1,
        role=role1,
        organization=organization1,
        assigned_by=user1
    )

@pytest.fixture
def user_role2(user2, role2, organization2):
    """Create a test user role for organization 2"""
    return UserRole.objects.create(
        user=user2,
        role=role2,
        organization=organization2,
        assigned_by=user2
    )

@pytest.fixture
def resource1(organization1):
    """Create a test resource for organization 1"""
    return Resource.objects.create(
        name="Test Resource 1",
        resource_type="test",
        organization=organization1
    )

@pytest.fixture
def resource2(organization2):
    """Create a test resource for organization 2"""
    return Resource.objects.create(
        name="Test Resource 2",
        resource_type="test",
        organization=organization2
    )

@pytest.mark.django_db
class TestOrganizationIsolationManager:
    """Tests for the organization isolation manager"""
    
    def test_for_organization(self, role1, role2, organization1):
        """Test filtering by organization"""
        roles = Role.objects.for_organization(organization1)
        assert role1 in roles
        assert role2 not in roles
    
    def test_for_user(self, role1, role2, user1, user2):
        """Test filtering by user"""
        roles = Role.objects.for_user(user1)
        assert role1 in roles
        assert role2 not in roles
        
        roles = Role.objects.for_user(user2)
        assert role1 not in roles
        assert role2 in roles
    
    def test_active(self, role1, role2):
        """Test filtering active objects"""
        role2.is_active = False
        role2.save()
        
        roles = Role.objects.active()
        assert role1 in roles
        assert role2 not in roles
    
    def test_inactive(self, role1, role2):
        """Test filtering inactive objects"""
        role2.is_active = False
        role2.save()
        
        roles = Role.objects.inactive()
        assert role1 not in roles
        assert role2 in roles
    
    def test_with_permission(self, role1, role2, permission1, permission2, user1, user2):
        """Test filtering by permission"""
        # Add permissions to roles
        role1.permissions.add(permission1)
        role2.permissions.add(permission2)
        
        # Test filtering by permission
        roles = Role.objects.with_permission(user1, permission1.code)
        assert role1 in roles
        assert role2 not in roles
        
        roles = Role.objects.with_permission(user2, permission2.code)
        assert role1 not in roles
        assert role2 in roles
    
    def test_cross_organization_isolation(self, role1, role2, user1, user2):
        """Test that users cannot access roles from other organizations"""
        roles = Role.objects.for_user(user1)
        assert role1 in roles
        assert role2 not in roles
        
        roles = Role.objects.for_user(user2)
        assert role1 not in roles
        assert role2 in roles
    
    def test_organization_context_isolation(self, organization1, organization2):
        """Test that organization contexts are isolated"""
        context1 = OrganizationContext.objects.create(
            name="Test Context 1",
            organization=organization1
        )
        
        context2 = OrganizationContext.objects.create(
            name="Test Context 2",
            organization=organization2
        )
        
        contexts = OrganizationContext.objects.for_organization(organization1)
        assert context1 in contexts
        assert context2 not in contexts
    
    def test_organization_context_hierarchy_isolation(self, organization1, organization2):
        """Test that organization context hierarchies are isolated"""
        parent1 = OrganizationContext.objects.create(
            name="Parent 1",
            organization=organization1
        )
        
        child1 = OrganizationContext.objects.create(
            name="Child 1",
            organization=organization1,
            parent=parent1
        )
        
        parent2 = OrganizationContext.objects.create(
            name="Parent 2",
            organization=organization2
        )
        
        # Try to create a child with a parent from another organization
        with pytest.raises(ValidationError):
            child2 = OrganizationContext(
                name="Child 2",
                organization=organization1,
                parent=parent2
            )
            child2.full_clean()
    
    def test_resource_isolation(self, resource1, resource2, user1, user2):
        """Test that resources are isolated"""
        resources = Resource.objects.for_user(user1)
        assert resource1 in resources
        assert resource2 not in resources
        
        resources = Resource.objects.for_user(user2)
        assert resource1 not in resources
        assert resource2 in resources
    
    def test_permission_isolation(self, permission1, permission2, user1, user2):
        """Test that permissions are isolated"""
        permissions = Permission.objects.for_user(user1)
        assert permission1 in permissions
        assert permission2 not in permissions
        
        permissions = Permission.objects.for_user(user2)
        assert permission1 not in permissions
        assert permission2 in permissions
    
    def test_user_role_isolation(self, user_role1, user_role2, user1, user2):
        """Test that user roles are isolated"""
        user_roles = UserRole.objects.for_user(user1)
        assert user_role1 in user_roles
        assert user_role2 not in user_roles
        
        user_roles = UserRole.objects.for_user(user2)
        assert user_role1 not in user_roles
        assert user_role2 in user_roles 