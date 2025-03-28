import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationViews:
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
    def organization(self, user):
        return Organization.objects.create(
            name='Test Organization',
            description='Test Description',
            created_by=user
        )

    @pytest.fixture
    def department(self, organization, user):
        return Department.objects.create(
            name='Test Department',
            organization=organization,
            description='Test Department Description',
            created_by=user
        )

    @pytest.fixture
    def team(self, department, user):
        return Team.objects.create(
            name='Test Team',
            department=department,
            description='Test Team Description',
            created_by=user
        )

    def test_organization_list_view(self, client, user):
        """Test organization list view"""
        client.force_login(user)
        response = client.get(reverse('entity:organization_list'))
        assert response.status_code == 200

    def test_organization_detail_view(self, client, user, organization):
        """Test organization detail view"""
        client.force_login(user)
        response = client.get(reverse('entity:organization_detail', kwargs={'pk': organization.pk}))
        assert response.status_code == 200

    def test_organization_create_view(self, client, user):
        """Test organization create view"""
        client.force_login(user)
        response = client.get(reverse('entity:organization_create'))
        assert response.status_code == 200

    def test_organization_update_view(self, client, user, organization):
        """Test organization update view"""
        client.force_login(user)
        response = client.get(reverse('entity:organization_update', kwargs={'pk': organization.pk}))
        assert response.status_code == 200

    def test_organization_delete_view(self, client, user, organization):
        """Test organization delete view"""
        client.force_login(user)
        response = client.get(reverse('entity:organization_delete', kwargs={'pk': organization.pk}))
        assert response.status_code == 200

    @patch('Apps.entity.views.render')
    def test_department_list_view(self, mock_render, client, user, organization):
        """Test department list view"""
        mock_render.return_value = HttpResponse()
        client.force_login(user)
        response = client.get(reverse('entity:department_list', kwargs={'org_pk': organization.pk}))
        assert response.status_code == 200

    @patch('Apps.entity.views.render')
    def test_department_detail_view(self, mock_render, client, user, department):
        """Test department detail view"""
        mock_render.return_value = HttpResponse()
        client.force_login(user)
        response = client.get(reverse('entity:department_detail', kwargs={'org_pk': department.organization.pk, 'pk': department.pk}))
        assert response.status_code == 200

    @patch('Apps.entity.views.render')
    def test_team_list_view(self, mock_render, client, user, department):
        """Test team list view"""
        mock_render.return_value = HttpResponse()
        client.force_login(user)
        response = client.get(reverse('entity:team_list', kwargs={'org_pk': department.organization.pk, 'dept_pk': department.pk}))
        assert response.status_code == 200

    @patch('Apps.entity.views.render')
    def test_team_detail_view(self, mock_render, client, user, team):
        """Test team detail view"""
        mock_render.return_value = HttpResponse()
        client.force_login(user)
        response = client.get(reverse('entity:team_detail', kwargs={'org_pk': team.department.organization.pk, 'dept_pk': team.department.pk, 'pk': team.pk}))
        assert response.status_code == 200 