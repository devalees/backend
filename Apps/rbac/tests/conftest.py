import os
import sys
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from Apps.rbac.models import Role, Permission
from Apps.entity.models import Organization, Department, Team, TeamMember
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Setup test environment
    """
    # Add any test environment setup here
    pass

@pytest.fixture
def common_permissions(organization):
    """Create common permissions used in tests"""
    permissions = {
        'view_project': Permission.objects.create(
            name='View Project',
            code='view_project',
            description='Can view projects',
            organization=organization
        ),
        'edit_project': Permission.objects.create(
            name='Edit Project',
            code='edit_project',
            description='Can edit projects',
            organization=organization
        ),
        'delete_project': Permission.objects.create(
            name='Delete Project',
            code='delete_project',
            description='Can delete projects',
            organization=organization
        )
    }
    return permissions

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
    django.setup() 