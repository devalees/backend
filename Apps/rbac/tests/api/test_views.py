from django.urls import reverse
import pytest
from django.contrib.auth import get_user_model
from Apps.rbac.models import Role, Permission, UserRole
from Apps.entity.models import Organization, Department, Team, TeamMember

User = get_user_model()

@pytest.fixture
def test_organization():
    return Organization.objects.create(
        name="Test Organization",
        description="Test Organization Description"
    )

@pytest.fixture
def test_department(test_organization):
    return Department.objects.create(
        name="Test Department",
        organization=test_organization,
        description="Test Department Description"
    )

@pytest.fixture
def test_team(test_department):
    return Team.objects.create(
        name="Test Team",
        department=test_department,
        description="Test Team Description"
    )

@pytest.fixture
def test_user(test_team):
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    # Create team membership to set organization
    TeamMember.objects.create(
        team=test_team,
        user=user,
        role=TeamMember.Role.MEMBER
    )
    return user

@pytest.fixture
def api_client(test_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client

@pytest.fixture
def test_role(test_organization):
    return Role.objects.create(
        name="Test Role",
        description="Test Role Description",
        organization=test_organization
    )

@pytest.fixture
def test_permission(test_organization):
    return Permission.objects.create(
        name="Test Permission",
        description="Test Permission Description",
        code="test.permission",
        organization=test_organization
    )

@pytest.mark.django_db
class TestRoleAPI:
    def test_role_list_endpoint(self, api_client, test_role):
        url = reverse('rbac:role-list')
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == test_role.name

    def test_role_create_endpoint(self, api_client, test_organization):
        url = reverse('rbac:role-list')
        data = {
            'name': 'New Role',
            'description': 'New Role Description',
            'organization': test_organization.id
        }
        response = api_client.post(url, data)
        assert response.status_code == 201
        assert Role.objects.filter(name='New Role').exists()

@pytest.mark.django_db
class TestPermissionAPI:
    def test_permission_list_endpoint(self, api_client, test_permission):
        url = reverse('rbac:permission-list')
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == test_permission.name

    def test_permission_create_endpoint(self, api_client, test_organization):
        url = reverse('rbac:permission-list')
        data = {
            'name': 'New Permission',
            'description': 'New Permission Description',
            'code': 'new.permission',
            'organization': test_organization.id
        }
        response = api_client.post(url, data)
        assert response.status_code == 201
        assert Permission.objects.filter(name='New Permission').exists() 