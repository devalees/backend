import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.entity.tests.factories import (
    OrganizationFactory, DepartmentFactory, TeamFactory, TeamMemberFactory
)
from Apps.users.tests.factories import UserFactory

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory(is_staff=True)
    api_client.force_authenticate(user=user)
    return api_client

@pytest.mark.django_db
class TestOrganizationViewSet:
    def test_list_organizations(self, authenticated_client):
        """Test listing organizations"""
        orgs = [OrganizationFactory() for _ in range(3)]
        url = reverse('organization-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_organization(self, authenticated_client):
        """Test creating an organization"""
        url = reverse('organization-list')
        data = {
            'name': 'Test Organization',
            'description': 'Test Description'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(name=data['name']).exists()

    def test_retrieve_organization(self, authenticated_client):
        """Test retrieving an organization"""
        org = OrganizationFactory()
        url = reverse('organization-detail', kwargs={'pk': org.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == org.name

    def test_update_organization(self, authenticated_client):
        """Test updating an organization"""
        org = OrganizationFactory()
        url = reverse('organization-detail', kwargs={'pk': org.pk})
        data = {'name': 'Updated Organization'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert org.name == data['name']

    def test_delete_organization(self, authenticated_client):
        """Test deleting an organization"""
        org = OrganizationFactory()
        url = reverse('organization-detail', kwargs={'pk': org.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        org.refresh_from_db()
        assert not org.is_active

@pytest.mark.django_db
class TestDepartmentViewSet:
    def test_list_departments(self, authenticated_client):
        """Test listing departments"""
        org = OrganizationFactory()
        depts = [DepartmentFactory(organization=org) for _ in range(3)]
        url = reverse('department-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_department(self, authenticated_client):
        """Test creating a department"""
        org = OrganizationFactory()
        url = reverse('department-list')
        data = {
            'name': 'Test Department',
            'description': 'Test Description',
            'organization': org.pk
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Department.objects.filter(name=data['name']).exists()

    def test_retrieve_department(self, authenticated_client):
        """Test retrieving a department"""
        dept = DepartmentFactory()
        url = reverse('department-detail', kwargs={'pk': dept.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == dept.name

    def test_update_department(self, authenticated_client):
        """Test updating a department"""
        dept = DepartmentFactory()
        url = reverse('department-detail', kwargs={'pk': dept.pk})
        data = {'name': 'Updated Department'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        dept.refresh_from_db()
        assert dept.name == data['name']

    def test_delete_department(self, authenticated_client):
        """Test deleting a department"""
        dept = DepartmentFactory()
        url = reverse('department-detail', kwargs={'pk': dept.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        dept.refresh_from_db()
        assert not dept.is_active

@pytest.mark.django_db
class TestTeamViewSet:
    def test_list_teams(self, authenticated_client):
        """Test listing teams"""
        dept = DepartmentFactory()
        teams = [TeamFactory(department=dept) for _ in range(3)]
        url = reverse('team-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_team(self, authenticated_client):
        """Test creating a team"""
        dept = DepartmentFactory()
        url = reverse('team-list')
        data = {
            'name': 'Test Team',
            'description': 'Test Description',
            'department': dept.pk
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Team.objects.filter(name=data['name']).exists()

    def test_retrieve_team(self, authenticated_client):
        """Test retrieving a team"""
        team = TeamFactory()
        url = reverse('team-detail', kwargs={'pk': team.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == team.name

    def test_update_team(self, authenticated_client):
        """Test updating a team"""
        team = TeamFactory()
        url = reverse('team-detail', kwargs={'pk': team.pk})
        data = {'name': 'Updated Team'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        team.refresh_from_db()
        assert team.name == data['name']

    def test_delete_team(self, authenticated_client):
        """Test deleting a team"""
        team = TeamFactory()
        url = reverse('team-detail', kwargs={'pk': team.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        team.refresh_from_db()
        assert not team.is_active

@pytest.mark.django_db
class TestTeamMemberViewSet:
    def test_list_team_members(self, authenticated_client):
        """Test listing team members"""
        team = TeamFactory()
        members = [TeamMemberFactory(team=team) for _ in range(3)]
        url = reverse('team-member-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_team_member(self, authenticated_client):
        """Test creating a team member"""
        team = TeamFactory()
        user = UserFactory()
        url = reverse('team-member-list')
        data = {
            'team': team.pk,
            'user_id': user.pk,
            'role': 'Leader'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert TeamMember.objects.filter(user=user, team=team).exists()

    def test_retrieve_team_member(self, authenticated_client):
        """Test retrieving a team member"""
        member = TeamMemberFactory()
        url = reverse('team-member-detail', kwargs={'pk': member.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == member.role

    def test_update_team_member(self, authenticated_client):
        """Test updating a team member"""
        member = TeamMemberFactory()
        url = reverse('team-member-detail', kwargs={'pk': member.pk})
        data = {'role': 'Manager'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.role == data['role']

    def test_delete_team_member(self, authenticated_client):
        """Test deleting a team member"""
        member = TeamMemberFactory()
        url = reverse('team-member-detail', kwargs={'pk': member.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        member.refresh_from_db()
        assert not member.is_active

    def test_unique_user_team_constraint(self, authenticated_client):
        """Test that a user cannot be added to the same team twice"""
        member = TeamMemberFactory()
        url = reverse('team-member-list')
        data = {
            'team': member.team.pk,
            'user_id': member.user.pk,
            'role': 'Member'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST 