import pytest
from rest_framework import status
from django.urls import reverse
from .conftest import user_role
from Apps.entity.models import TeamMember, Department, Team

@pytest.mark.django_db
class TestUserRoleViewSet:
    def test_list_user_roles(self, client, user, organization, role):
        """Test listing user roles"""
        # Create a user role
        user_role = user.user_roles.create(
            role=role,
            organization=organization,
            assigned_by=user
        )

        # Authenticate and make request
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == user_role.id

    def test_create_user_role(self, client, user, organization, role):
        """Test creating a user role"""
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-list')
        data = {
            'user': user.id,
            'role': role.id,
            'organization': organization.id
        }
        response = client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == user.id
        assert response.data['role'] == role.id
        assert response.data['assigned_by'] == user.id

    def test_update_user_role(self, client, user, user_role):
        """Test updating a user role"""
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-detail', args=[user_role.id])
        data = {
            'notes': 'Updated notes'
        }
        response = client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['notes'] == 'Updated notes'

    def test_activate_user_role(self, client, user, user_role):
        """Test activating a user role"""
        user_role.deactivate()
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-activate', args=[user_role.id])
        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        user_role.refresh_from_db()
        assert user_role.is_active is True
        assert user_role.deactivated_at is None

    def test_deactivate_user_role(self, client, user, user_role):
        """Test deactivating a user role"""
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-deactivate', args=[user_role.id])
        response = client.post(url)

        assert response.status_code == status.HTTP_200_OK
        user_role.refresh_from_db()
        assert user_role.is_active is False
        assert user_role.deactivated_at is not None

    def test_delegate_role(self, client, user, user_role, organization):
        """Test delegating a role to another user"""
        # Create another user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = User.objects.create_user(
            username='targetuser',
            email='target@example.com',
            password='testpass123'
        )

        # Add user to organization through team membership
        department = organization.departments.first() or Department.objects.create(
            name='Test Department',
            organization=organization
        )
        team = department.teams.first() or Team.objects.create(
            name='Test Team',
            department=department
        )
        TeamMember.objects.create(
            team=team,
            user=target_user,
            role=TeamMember.Role.MEMBER
        )

        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-delegate', args=[user_role.id])
        data = {'user': target_user.id}
        response = client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['user'] == target_user.id
        assert response.data['delegated_by'] == user_role.id
        assert response.data['is_delegated'] is True

    def test_filter_user_roles(self, client, user, user_role):
        """Test filtering user roles"""
        client.force_authenticate(user=user)
        url = reverse('rbac:userrole-list')
        response = client.get(f"{url}?is_active=true")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == user_role.id

    def test_organization_isolation(self, client, user, user_role):
        """Test that users can only see roles in their organization"""
        # Create another organization and user
        from Apps.entity.models import Organization
        other_org = Organization.objects.create(name='Other Organization')
        
        # Create department and team for other organization
        department = Department.objects.create(
            name='Other Department',
            organization=other_org
        )
        team = Team.objects.create(
            name='Other Team',
            department=department
        )
        
        # Create user in other organization
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Add user to other organization through team membership
        TeamMember.objects.create(
            team=team,
            user=other_user,
            role=TeamMember.Role.MEMBER
        )

        client.force_authenticate(user=other_user)
        url = reverse('rbac:userrole-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0

    def test_permission_required(self, client, user_role):
        """Test that authentication is required"""
        url = reverse('rbac:userrole-list')
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED 