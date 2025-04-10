from rest_framework.test import APIClient
from rest_framework import status
import pytest
from django.urls import reverse
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.rbac.models import Role, Permission
from Apps.users.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(organization):
    # Create user
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )
    
    # Create department
    department = Department.objects.create(
        name='Test Department',
        organization=organization
    )
    
    # Create team
    team = Team.objects.create(
        name='Test Team',
        department=department
    )
    
    # Create team membership
    TeamMember.objects.create(
        user=user,
        team=team,
        role=TeamMember.Role.ADMIN
    )
    
    return user

@pytest.mark.django_db
class TestResponseFormat:
    @pytest.fixture(autouse=True)
    def setup(self, api_client, test_user):
        api_client.force_authenticate(user=test_user)
        self.user = test_user

    def test_role_list_response_format(self, api_client, organization):
        """Test the format of role list response."""
        # Create a test role
        Role.objects.create(
            name='Test Role',
            description='Test Description',
            organization=organization
        )

        url = reverse('rbac:role-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert 'meta' in response.json()
        assert 'pagination' in response.json()['meta']
        
        # Check pagination metadata
        pagination = response.json()['meta']['pagination']
        assert 'count' in pagination
        assert 'total_pages' in pagination
        assert 'current_page' in pagination
        assert 'page_size' in pagination
        assert 'has_next' in pagination
        assert 'has_previous' in pagination

    def test_role_create_response_format(self, api_client, organization):
        """Test the format of role create response."""
        url = reverse('rbac:role-list')
        data = {
            'name': 'New Role',
            'description': 'New Role Description',
            'organization': organization.id
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'data' in response.json()
        assert response.json()['data']['name'] == 'New Role'

    def test_role_update_response_format(self, api_client, organization):
        """Test the format of role update response."""
        role = Role.objects.create(
            name='Test Role',
            description='Test Description',
            organization=organization
        )

        url = reverse('rbac:role-detail', kwargs={'pk': role.pk})
        data = {
            'name': 'Updated Role',
            'description': 'Updated Description',
            'organization': organization.id
        }
        response = api_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.json()
        assert response.json()['data']['name'] == 'Updated Role'

    def test_role_delete_response_format(self, api_client, organization):
        """Test the format of role delete response."""
        role = Role.objects.create(
            name='Test Role',
            description='Test Description',
            organization=organization
        )

        url = reverse('rbac:role-detail', kwargs={'pk': role.pk})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_error_response_format(self, api_client, organization):
        """Test the format of error responses."""
        url = reverse('rbac:role-list')
        data = {
            'name': '',  # Invalid: empty name
            'organization': organization.id
        }
        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.json()
        assert 'name' in response.json()['errors'] 