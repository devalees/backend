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
    return api_client, user

@pytest.mark.django_db
class TestOrganizationViewSet:
    def test_list_organizations(self, authenticated_client):
        """Test listing organizations"""
        orgs = [OrganizationFactory() for _ in range(3)]
        url = reverse('entity:organization-list')
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_organization(self, authenticated_client):
        """Test creating an organization."""
        client, user = authenticated_client
        data = {
            'name': 'Test Organization',
            'description': 'Test Description'
        }
        
        url = reverse('entity:organization-list')
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.all_objects.filter(name=data['name']).exists()

    def test_retrieve_organization(self, authenticated_client):
        """Test retrieving an organization"""
        org = OrganizationFactory()
        url = reverse('entity:organization-detail', kwargs={'pk': org.pk})
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == org.name

    def test_update_organization(self, authenticated_client):
        """Test updating an organization"""
        org = OrganizationFactory()
        url = reverse('entity:organization-detail', kwargs={'pk': org.pk})
        data = {'name': 'Updated Organization'}
        response = authenticated_client[0].patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert org.name == data['name']

    def test_delete_organization(self, authenticated_client):
        """Test deleting an organization"""
        org = OrganizationFactory()
        url = reverse('entity:organization-detail', kwargs={'pk': org.pk})
        response = authenticated_client[0].delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        org.refresh_from_db()
        assert not org.is_active

@pytest.mark.django_db
class TestDepartmentViewSet:
    def test_list_departments(self, authenticated_client):
        """Test listing departments"""
        org = OrganizationFactory()
        depts = [DepartmentFactory(organization=org) for _ in range(3)]
        url = reverse('entity:department-list')
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_department(self, authenticated_client):
        """Test creating a department"""
        org = OrganizationFactory()
        url = reverse('entity:department-list')
        data = {
            'name': 'Test Department',
            'description': 'Test Description',
            'organization': org.pk
        }
        response = authenticated_client[0].post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Department.objects.filter(name=data['name']).exists()

    def test_retrieve_department(self, authenticated_client):
        """Test retrieving a department"""
        dept = DepartmentFactory()
        url = reverse('entity:department-detail', kwargs={'pk': dept.pk})
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == dept.name

    def test_update_department(self, authenticated_client):
        """Test updating a department"""
        dept = DepartmentFactory()
        url = reverse('entity:department-detail', kwargs={'pk': dept.pk})
        data = {'name': 'Updated Department'}
        response = authenticated_client[0].patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        dept.refresh_from_db()
        assert dept.name == data['name']

    def test_delete_department(self, authenticated_client):
        """Test deleting a department"""
        dept = DepartmentFactory()
        url = reverse('entity:department-detail', kwargs={'pk': dept.pk})
        response = authenticated_client[0].delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        dept.refresh_from_db()
        assert not dept.is_active

@pytest.mark.django_db
class TestTeamViewSet:
    def test_list_teams(self, authenticated_client):
        """Test listing teams"""
        dept = DepartmentFactory()
        teams = [TeamFactory(department=dept) for _ in range(3)]
        url = reverse('entity:team-list')
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_team(self, authenticated_client):
        """Test creating a team"""
        client, user = authenticated_client
        department = DepartmentFactory()
        data = {
            'name': 'Test Team',
            'description': 'Test Description',
            'department': department.id
        }
        
        url = reverse('entity:team-list')
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Team.all_objects.filter(name=data['name']).exists()

    def test_retrieve_team(self, authenticated_client):
        """Test retrieving a team"""
        team = TeamFactory()
        url = reverse('entity:team-detail', kwargs={'pk': team.pk})
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == team.name

    def test_update_team(self, authenticated_client):
        """Test updating a team"""
        team = TeamFactory()
        url = reverse('entity:team-detail', kwargs={'pk': team.pk})
        data = {'name': 'Updated Team'}
        response = authenticated_client[0].patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        team.refresh_from_db()
        assert team.name == data['name']

    def test_delete_team(self, authenticated_client):
        """Test deleting a team"""
        team = TeamFactory()
        url = reverse('entity:team-detail', kwargs={'pk': team.pk})
        response = authenticated_client[0].delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        team.refresh_from_db()
        assert not team.is_active

@pytest.mark.django_db
class TestTeamMemberViewSet:
    def test_list_team_members(self, authenticated_client):
        """Test listing team members"""
        team = TeamFactory()
        members = [TeamMemberFactory(team=team) for _ in range(3)]
        url = reverse('entity:team-member-list')
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_team_member(self, authenticated_client):
        """Test creating a team member."""
        client, user = authenticated_client
        team = TeamFactory()
        user = UserFactory()
        data = {
            'user_id': user.id,
            'team': team.id,
            'role': 'member'
        }
        
        url = reverse('entity:team-member-list')
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert TeamMember.all_objects.filter(user=user, team=team).exists()

    def test_retrieve_team_member(self, authenticated_client):
        """Test retrieving a team member"""
        member = TeamMemberFactory()
        url = reverse('entity:team-member-detail', kwargs={'pk': member.pk})
        response = authenticated_client[0].get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == member.role

    def test_update_team_member(self, authenticated_client):
        """Test updating a team member"""
        member = TeamMemberFactory()
        url = reverse('entity:team-member-detail', kwargs={'pk': member.pk})
        data = {'role': 'Manager'}
        response = authenticated_client[0].patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.role == data['role']

    def test_delete_team_member(self, authenticated_client):
        """Test deleting a team member"""
        member = TeamMemberFactory()
        url = reverse('entity:team-member-detail', kwargs={'pk': member.pk})
        response = authenticated_client[0].delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        member.refresh_from_db()
        assert not member.is_active

    def test_unique_user_team_constraint(self, authenticated_client):
        """Test that a user cannot be added to the same team twice"""
        member = TeamMemberFactory()
        url = reverse('entity:team-member-list')
        data = {
            'team': member.team.pk,
            'user_id': member.user.pk,
            'role': 'Member'
        }
        response = authenticated_client[0].post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST 