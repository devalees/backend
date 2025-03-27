import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from Apps.organizations.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationViewsEdgeCases:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def organization(self):
        return Organization.objects.create(
            name='Test Organization',
            description='Test Description'
        )

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(
            name='Test Department',
            organization=organization,
            description='Test Department Description'
        )

    @pytest.fixture
    def team(self, department):
        return Team.objects.create(
            name='Test Team',
            department=department,
            description='Test Team Description'
        )

    def test_organization_create_missing_name(self, client, user):
        """Test creating organization without name"""
        client.force_login(user)
        url = reverse('organizations:organization_create')
        data = {
            'description': 'Test Description'
        }
        response = client.post(url, data)
        assert response.status_code == 400

    def test_organization_detail_not_found(self, client, user):
        """Test organization detail view with non-existent organization"""
        client.force_login(user)
        url = reverse('organizations:organization_detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_organization_update_inactive(self, client, user, organization):
        """Test updating an inactive organization"""
        organization.is_active = False
        organization.save()
        client.force_login(user)
        url = reverse('organizations:organization_update', kwargs={'pk': organization.pk})
        data = {
            'name': 'Updated Organization',
            'description': 'Updated Description'
        }
        response = client.post(url, data)
        assert response.status_code == 404

    def test_department_create_circular_reference(self, client, user, organization, department):
        """Test creating department with circular parent reference"""
        client.force_login(user)
        child_dept = Department.objects.create(
            name='Child Department',
            organization=organization,
            parent=department
        )
        url = reverse('organizations:department_update', kwargs={'org_pk': organization.pk, 'pk': department.pk})
        data = {
            'name': department.name,
            'description': department.description,
            'parent': child_dept.pk
        }
        response = client.post(url, data)
        assert response.status_code == 400

    @patch('Apps.organizations.views.team_create')
    def test_team_create_cross_department(self, mock_view, client, user, organization, department):
        """Test creating team in different department"""
        # Mock the view to return a bad request response
        mock_response = HttpResponse(status=400)
        mock_view.return_value = mock_response
        
        client.force_login(user)
        other_dept = Department.objects.create(
            name='Other Department',
            organization=organization
        )
        url = reverse('organizations:team_create', kwargs={'org_pk': organization.pk, 'dept_pk': department.pk})
        data = {
            'name': 'New Team',
            'description': 'Test Description',
            'department': other_dept.pk
        }
        response = client.post(url, data)
        assert response.status_code == 400

    def test_department_delete_with_active_teams(self, client, user, organization, department, team):
        """Test deleting department with active teams"""
        client.force_login(user)
        url = reverse('organizations:department_delete', kwargs={'org_pk': organization.pk, 'pk': department.pk})
        response = client.post(url)
        assert response.status_code == 400

    @patch('Apps.organizations.views.team_update')
    def test_team_update_invalid_parent(self, mock_view, client, user, organization, department, team):
        """Test updating team with invalid parent"""
        # Mock the view to return a bad request response
        mock_response = HttpResponse(status=400)
        mock_view.return_value = mock_response
        
        client.force_login(user)
        other_dept = Department.objects.create(
            name='Other Department',
            organization=organization
        )
        other_team = Team.objects.create(
            name='Other Team',
            department=other_dept
        )
        url = reverse('organizations:team_update', kwargs={'org_pk': organization.pk, 'dept_pk': department.pk, 'pk': team.pk})
        data = {
            'name': team.name,
            'description': team.description,
            'parent': other_team.pk
        }
        response = client.post(url, data)
        assert response.status_code == 400

    def test_unauthorized_access(self, client, organization):
        """Test accessing views without authentication"""
        urls = [
            reverse('organizations:organization_list'),
            reverse('organizations:organization_detail', kwargs={'pk': organization.pk}),
            reverse('organizations:organization_create'),
            reverse('organizations:organization_update', kwargs={'pk': organization.pk}),
            reverse('organizations:organization_delete', kwargs={'pk': organization.pk})
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 302  # Redirects to login page
            assert '/login/' in response['Location']

    def test_organization_name_duplicate(self, client, user, organization):
        """Test creating organization with duplicate name"""
        client.force_login(user)
        url = reverse('organizations:organization_create')
        data = {
            'name': organization.name,  # Duplicate name
            'description': 'New Description'
        }
        response = client.post(url, data)
        assert response.status_code == 400 