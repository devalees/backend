import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from Apps.rbac.models import Role, Permission, UserRole
from Apps.entity.models import Organization, TeamMember, Department, Team
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Org")

@pytest.fixture
def admin_user(organization):
    user = User.objects.create_user(
        username="admin",
        email="admin@test.com",
        password="testpass123"
    )
    department = Department.objects.create(
        name="Test Department",
        organization=organization
    )
    team = Team.objects.create(
        name="Test Team",
        department=department
    )
    TeamMember.objects.create(
        user=user,
        team=team,
        is_active=True
    )
    return user

@pytest.fixture
def role(organization):
    return Role.objects.create(
        name="Test Role",
        organization=organization
    )

@pytest.fixture
def permission(organization):
    return Permission.objects.create(
        name="Test Permission",
        code="test.permission",
        organization=organization
    )

@pytest.mark.django_db
class TestSuccessResponseFormatting:
    """Test cases for standardized success responses"""
    
    def test_role_list_response_format(self, client, admin_user, organization, role):
        """Test that role list endpoint returns properly formatted response"""
        client.force_authenticate(user=admin_user)
        url = reverse('rbac:role-list')
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'meta' in response.data
        assert 'links' in response.data
        
        # Check data structure
        assert isinstance(response.data['data'], list)
        assert len(response.data['data']) > 0
        
        # Check first role data structure
        role_data = response.data['data'][0]
        assert 'id' in role_data
        assert 'type' in role_data
        assert role_data['type'] == 'roles'
        assert 'attributes' in role_data
        assert 'relationships' in role_data
        
        # Check meta structure
        assert 'count' in response.data['meta']
        assert 'total_pages' in response.data['meta']
        assert 'current_page' in response.data['meta']
        assert 'page_size' in response.data['meta']
        
        # Check links structure
        assert 'self' in response.data['links']
        assert 'first' in response.data['links']
        assert 'last' in response.data['links']
        assert 'next' in response.data['links']
        assert 'prev' in response.data['links']
    
    def test_role_detail_response_format(self, client, admin_user, role):
        """Test that role detail endpoint returns properly formatted response"""
        client.force_authenticate(user=admin_user)
        url = reverse('rbac:role-detail', kwargs={'pk': role.pk})
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'included' in response.data
        
        # Check data structure
        assert 'id' in response.data['data']
        assert 'type' in response.data['data']
        assert response.data['data']['type'] == 'roles'
        assert 'attributes' in response.data['data']
        assert 'relationships' in response.data['data']
        
        # Check attributes
        attributes = response.data['data']['attributes']
        assert 'name' in attributes
        assert 'description' in attributes
        assert 'is_active' in attributes
        
        # Check relationships
        relationships = response.data['data']['relationships']
        assert 'organization' in relationships
        assert 'parent' in relationships
        assert 'permissions' in relationships
    
    def test_permission_list_response_format(self, client, admin_user, organization, permission):
        """Test that permission list endpoint returns properly formatted response"""
        client.force_authenticate(user=admin_user)
        url = reverse('rbac:permission-list')
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'meta' in response.data
        assert 'links' in response.data
        
        # Check data structure
        assert isinstance(response.data['data'], list)
        assert len(response.data['data']) > 0
        
        # Check first permission data structure
        perm_data = response.data['data'][0]
        assert 'id' in perm_data
        assert 'type' in perm_data
        assert perm_data['type'] == 'permissions'
        assert 'attributes' in perm_data
        assert 'relationships' in perm_data
        
        # Check meta structure
        assert 'count' in response.data['meta']
        assert 'total_pages' in response.data['meta']
        assert 'current_page' in response.data['meta']
        assert 'page_size' in response.data['meta']
        
        # Check links structure
        assert 'self' in response.data['links']
        assert 'first' in response.data['links']
        assert 'last' in response.data['links']
        assert 'next' in response.data['links']
        assert 'prev' in response.data['links']
    
    def test_permission_detail_response_format(self, client, admin_user, permission):
        """Test that permission detail endpoint returns properly formatted response"""
        client.force_authenticate(user=admin_user)
        url = reverse('rbac:permission-detail', kwargs={'pk': permission.pk})
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'included' in response.data
        
        # Check data structure
        assert 'id' in response.data['data']
        assert 'type' in response.data['data']
        assert response.data['data']['type'] == 'permissions'
        assert 'attributes' in response.data['data']
        assert 'relationships' in response.data['data']
        
        # Check attributes
        attributes = response.data['data']['attributes']
        assert 'name' in attributes
        assert 'description' in attributes
        assert 'code' in attributes
        assert 'is_active' in attributes
        
        # Check relationships
        relationships = response.data['data']['relationships']
        assert 'organization' in relationships 