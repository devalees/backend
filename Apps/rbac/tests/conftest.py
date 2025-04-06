import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from Apps.rbac.models import Role, Permission
from Apps.entity.models import Organization, Department, Team, TeamMember

User = get_user_model()

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def organization():
    return Organization.objects.create(name='Test Organization')

@pytest.fixture
def user(organization):
    # Create a department for the organization
    department = Department.objects.create(
        name='Test Department',
        organization=organization
    )
    
    # Create a team in the department
    team = Team.objects.create(
        name='Test Team',
        department=department
    )
    
    # Create the user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create a team membership to associate the user with the organization
    TeamMember.objects.create(
        team=team,
        user=user,
        role=TeamMember.Role.MEMBER
    )
    
    return user

@pytest.fixture
def role(organization):
    return Role.objects.create(
        name='Test Role',
        organization=organization
    )

@pytest.fixture
def permission(organization):
    return Permission.objects.create(
        name='Test Permission',
        code='test.permission',
        organization=organization
    )

@pytest.fixture
def user_role(organization, user, role):
    from Apps.rbac.models import UserRole
    return UserRole.objects.create(
        user=user,
        role=role,
        organization=organization,
        assigned_by=user
    )

@pytest.fixture
def test_organization():
    """Create a test organization"""
    # This will be replaced with actual Organization model when implemented
    return {'id': 1, 'name': 'Test Organization'}

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test"""
    cache.clear() 