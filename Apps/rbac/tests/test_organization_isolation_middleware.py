import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.urls import reverse
from Apps.rbac.middleware import OrganizationIsolationMiddleware
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

@pytest.fixture
def organization():
    """Create a test organization"""
    return Organization.objects.create(
        name="Test Organization",
        description="Test organization"
    )

@pytest.fixture
def user(organization):
    """Create a test user"""
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
        role=TeamMember.Role.MEMBER,
        is_active=True
    )
    
    return user

@pytest.fixture
def other_organization():
    """Create another test organization"""
    return Organization.objects.create(
        name="Other Organization",
        description="Other organization"
    )

@pytest.fixture
def other_user(other_organization):
    """Create another test user"""
    # Create a department for the organization
    department = Department.objects.create(
        name='Test Department',
        organization=other_organization
    )
    
    # Create a team in the department
    team = Team.objects.create(
        name='Test Team',
        department=department
    )
    
    # Create the user
    user = User.objects.create_user(
        username='otheruser',
        email='other@example.com',
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
def request_factory():
    """Create a request factory"""
    return RequestFactory()

@pytest.mark.django_db
class TestOrganizationIsolationMiddleware:
    """Tests for the organization isolation middleware"""
    
    def test_middleware_initialization(self):
        """Test that the middleware can be initialized"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        assert middleware is not None
    
    def test_middleware_call(self, request_factory):
        """Test that the middleware can be called"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/')
        response = middleware(request)
        assert response is None
    
    def test_middleware_process_view_admin(self, request_factory, user):
        """Test that the middleware skips admin views"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/admin/')
        request.user = user
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_auth(self, request_factory, user):
        """Test that the middleware skips auth views"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/auth/')
        request.user = user
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_unauthenticated(self, request_factory):
        """Test that the middleware skips unauthenticated users"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/')
        request.user = AnonymousUser()
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_no_organization(self, request_factory, user):
        """Test that the middleware skips requests without organization_id"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/')
        request.user = user
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_invalid_organization(self, request_factory, user):
        """Test that the middleware skips requests with invalid organization_id"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/?organization_id=999')
        request.user = user
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_user_in_organization(self, request_factory, user, organization):
        """Test that the middleware allows users in the organization"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get(f'/?organization_id={organization.id}')
        request.user = user
        response = middleware.process_view(request, None, None, None)
        assert response is None
    
    def test_middleware_process_view_user_not_in_organization(self, request_factory, user, other_organization):
        """Test that the middleware denies users not in the organization"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get(f'/?organization_id={other_organization.id}')
        request.user = user
        
        with pytest.raises(PermissionDenied):
            middleware.process_view(request, None, None, None)
    
    def test_middleware_process_template_response(self, request_factory):
        """Test that the middleware can process template responses"""
        middleware = OrganizationIsolationMiddleware(lambda r: None)
        request = request_factory.get('/')
        response = middleware.process_template_response(request, None)
        assert response is None 