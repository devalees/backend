import pytest
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from Apps.rbac.models import OrganizationContext, Role, Permission, UserRole, Resource
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
        name='Role 1',
        organization=organization1
    )

@pytest.fixture
def role2(organization2):
    """Create a role in organization 2"""
    return Role.objects.create(
        name='Role 2',
        organization=organization2
    )

@pytest.fixture
def permission1(organization1):
    """Create a permission in organization 1"""
    return Permission.objects.create(
        name='Permission 1',
        code='permission1',
        organization=organization1
    )

@pytest.fixture
def permission2(organization2):
    """Create a permission in organization 2"""
    return Permission.objects.create(
        name='Permission 2',
        code='permission2',
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
        name='Resource 1',
        resource_type='test',
        organization=organization1
    )

@pytest.fixture
def resource2(organization2):
    """Create a resource in organization 2"""
    return Resource.objects.create(
        name='Resource 2',
        resource_type='test',
        organization=organization2
    )

@pytest.mark.django_db
class TestOrganizationIsolation:
    """Tests for organization isolation in the RBAC system"""
    
    def test_role_organization_isolation(self, organization1, organization2, role1, role2):
        """Test that roles are isolated by organization"""
        # Verify roles belong to different organizations
        assert role1.organization == organization1
        assert role2.organization == organization2
        
        # Verify roles can't be accessed across organizations
        assert Role.objects.filter(organization=organization1).count() == 1
        assert Role.objects.filter(organization=organization2).count() == 1
        
        # Verify roles can't be assigned across organizations
        with pytest.raises(ValidationError):
            role1.organization = organization2
            role1.full_clean()
    
    def test_permission_organization_isolation(self, organization1, organization2, permission1, permission2):
        """Test that permissions are isolated by organization"""
        # Verify permissions belong to different organizations
        assert permission1.organization == organization1
        assert permission2.organization == organization2
        
        # Verify permissions can't be accessed across organizations
        assert Permission.objects.filter(organization=organization1).count() == 1
        assert Permission.objects.filter(organization=organization2).count() == 1
        
        # Verify permissions can't be assigned across organizations
        with pytest.raises(ValidationError):
            permission1.organization = organization2
            permission1.full_clean()
    
    def test_user_role_organization_isolation(self, organization1, organization2, user1, user2, role1, role2):
        """Test that user roles are isolated by organization"""
        # Create user roles in different organizations
        user_role1 = UserRole.objects.create(
            user=user1,
            role=role1,
            organization=organization1,
            assigned_by=user1
        )
        
        user_role2 = UserRole.objects.create(
            user=user2,
            role=role2,
            organization=organization2,
            assigned_by=user2
        )
        
        # Verify user roles belong to different organizations
        assert user_role1.organization == organization1
        assert user_role2.organization == organization2
        
        # Verify user roles can't be accessed across organizations
        assert UserRole.objects.filter(organization=organization1).count() == 1
        assert UserRole.objects.filter(organization=organization2).count() == 1
        
        # Verify user roles can't be assigned across organizations
        with pytest.raises(ValidationError):
            user_role1.organization = organization2
            user_role1.full_clean()
    
    def test_resource_organization_isolation(self, organization1, organization2, resource1, resource2):
        """Test that resources are isolated by organization"""
        # Verify resources belong to different organizations
        assert resource1.organization == organization1
        assert resource2.organization == organization2
        
        # Verify resources can't be accessed across organizations
        assert Resource.objects.filter(organization=organization1).count() == 1
        assert Resource.objects.filter(organization=organization2).count() == 1
        
        # Verify resources can't be assigned across organizations
        with pytest.raises(ValidationError):
            resource1.organization = organization2
            resource1.full_clean()
    
    def test_cross_organization_access_denied(self, organization1, organization2, user1, role1, permission1, resource2):
        """Test that users can't access resources from other organizations"""
        # Assign permission to role
        role1.permissions.add(permission1)
        
        # Create user role
        UserRole.objects.create(
            user=user1,
            role=role1,
            organization=organization1,
            assigned_by=user1
        )
        
        # Verify user can't access resource from another organization
        assert not resource2.has_access(user1, 'read')
    
    def test_organization_context_isolation(self, organization1, organization2):
        """Test that organization contexts are isolated by organization"""
        # Create organization contexts in different organizations
        context1 = OrganizationContext.objects.create(
            name='Context 1',
            organization=organization1
        )
        
        context2 = OrganizationContext.objects.create(
            name='Context 2',
            organization=organization2
        )
        
        # Verify contexts belong to different organizations
        assert context1.organization == organization1
        assert context2.organization == organization2
        
        # Verify contexts can't be accessed across organizations
        assert OrganizationContext.objects.filter(organization=organization1).count() == 1
        assert OrganizationContext.objects.filter(organization=organization2).count() == 1
        
        # Verify contexts can't be assigned across organizations
        with pytest.raises(ValidationError):
            context1.organization = organization2
            context1.full_clean()
    
    def test_organization_context_hierarchy_isolation(self, organization1, organization2):
        """Test that organization context hierarchies are isolated by organization"""
        # Create parent and child contexts in organization 1
        parent1 = OrganizationContext.objects.create(
            name='Parent 1',
            organization=organization1
        )
        
        child1 = OrganizationContext.objects.create(
            name='Child 1',
            organization=organization1,
            parent=parent1
        )
        
        # Create parent and child contexts in organization 2
        parent2 = OrganizationContext.objects.create(
            name='Parent 2',
            organization=organization2
        )
        
        child2 = OrganizationContext.objects.create(
            name='Child 2',
            organization=organization2,
            parent=parent2
        )
        
        # Verify child contexts belong to the same organization as their parents
        assert child1.organization == parent1.organization
        assert child2.organization == parent2.organization
        
        # Verify child contexts can't have parents from different organizations
        with pytest.raises(ValidationError):
            child1.parent = parent2
            child1.full_clean()
    
    def test_organization_data_isolation(self, organization1, organization2, user1, user2, role1, role2, permission1, permission2, resource1, resource2):
        """Test that data is isolated by organization"""
        # Assign permissions to roles
        role1.permissions.add(permission1)
        role2.permissions.add(permission2)
        
        # Create user roles
        UserRole.objects.create(
            user=user1,
            role=role1,
            organization=organization1,
            assigned_by=user1
        )
        
        UserRole.objects.create(
            user=user2,
            role=role2,
            organization=organization2,
            assigned_by=user2
        )
        
        # Grant access to resources
        resource1.grant_access(user1, 'read')
        resource2.grant_access(user2, 'read')
        
        # Verify users can only access data from their organizations
        assert Role.objects.filter(organization=organization1).count() == 1
        assert Role.objects.filter(organization=organization2).count() == 1
        
        assert Permission.objects.filter(organization=organization1).count() == 1
        assert Permission.objects.filter(organization=organization2).count() == 1
        
        assert Resource.objects.filter(organization=organization1).count() == 1
        assert Resource.objects.filter(organization=organization2).count() == 1
        
        # Verify users can only access resources from their organizations
        assert resource1.has_access(user1, 'read')
        assert not resource1.has_access(user2, 'read')
        
        assert resource2.has_access(user2, 'read')
        assert not resource2.has_access(user1, 'read')
    
    def test_organization_query_isolation(self, organization1, organization2, user1, user2, role1, role2, permission1, permission2, resource1, resource2):
        """Test that queries are isolated by organization"""
        # Assign permissions to roles
        role1.permissions.add(permission1)
        role2.permissions.add(permission2)
        
        # Create user roles
        UserRole.objects.create(
            user=user1,
            role=role1,
            organization=organization1,
            assigned_by=user1
        )
        
        UserRole.objects.create(
            user=user2,
            role=role2,
            organization=organization2,
            assigned_by=user2
        )
        
        # Verify users can only query data from their organizations
        assert Role.objects.filter(organization=organization1).count() == 1
        assert Role.objects.filter(organization=organization2).count() == 1
        
        assert Permission.objects.filter(organization=organization1).count() == 1
        assert Permission.objects.filter(organization=organization2).count() == 1
        
        assert Resource.objects.filter(organization=organization1).count() == 1
        assert Resource.objects.filter(organization=organization2).count() == 1
        
        # Verify users can only query resources from their organizations
        assert Resource.objects.filter(organization=organization1).count() == 1
        assert Resource.objects.filter(organization=organization2).count() == 1 