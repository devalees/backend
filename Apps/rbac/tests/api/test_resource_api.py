import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from Apps.rbac.models import Resource
from Apps.entity.models import Organization, Department, Team, TeamMember
from datetime import datetime

User = get_user_model()

@pytest.mark.django_db
class TestResourceAPI:
    """Test suite for Resource API endpoints"""
    
    def test_resource_list_endpoint(self, api_client, test_resource):
        """Test that resource list endpoint returns correct data"""
        url = reverse('rbac:resource-list')
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == test_resource.name
    
    def test_resource_create_endpoint(self, client, test_organization, test_user):
        """Test that resource can be created via API"""
        client.force_authenticate(user=test_user)
        url = reverse('rbac:resource-list')
        data = {
            'data': {
                'type': 'resources',
                'attributes': {
                    'name': 'Test Resource',
                    'resource_type': 'document',
                    'is_active': True
                },
                'relationships': {
                    'organization': {
                        'data': {
                            'type': 'organizations',
                            'id': str(test_organization.id)
                        }
                    }
                }
            }
        }
        response = client.post(url, data, format='json')
        print(f"Create response content: {response.content}")  # Debug print
        assert response.status_code == 201
        assert response.data['data']['attributes']['name'] == data['data']['attributes']['name']
    
    def test_resource_retrieve_endpoint(self, api_client, test_resource):
        """Test that resource can be retrieved via API"""
        url = reverse('rbac:resource-detail', kwargs={'pk': test_resource.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['data']['attributes']['name'] == test_resource.name
    
    def test_resource_update_endpoint(self, client, organization, test_user):
        """Test that resource can be updated via API"""
        # Create a department for the test organization
        department = Department.objects.create(
            name=f'Test Department {datetime.now().timestamp()}',
            organization=organization
        )
        
        # Create a team in the department
        team = Team.objects.create(
            name=f'Test Team {datetime.now().timestamp()}',
            department=department
        )
        
        # Create a team membership to associate the user with the test organization
        TeamMember.objects.create(
            team=team,
            user=test_user,
            role=TeamMember.Role.MEMBER,
            is_active=True
        )
        
        client.force_authenticate(user=test_user)
        # First create a resource
        create_url = reverse('rbac:resource-list')
        create_data = {
            'data': {
                'type': 'resources',
                'attributes': {
                    'name': 'Original Resource',
                    'resource_type': 'document',
                    'is_active': True
                },
                'relationships': {
                    'organization': {
                        'data': {
                            'type': 'organizations',
                            'id': str(organization.id)
                        }
                    }
                }
            }
        }
        create_response = client.post(create_url, create_data, format='json')
        print(f"Create response content: {create_response.content}")  # Debug print
        assert create_response.status_code == 201
        resource_id = create_response.data['data']['id']

        # Update the resource
        update_url = reverse('rbac:resource-detail', kwargs={'pk': resource_id})
        update_data = {
            'data': {
                'type': 'resources',
                'id': resource_id,
                'attributes': {
                    'name': 'Updated Resource',
                    'resource_type': 'document',
                    'is_active': True
                },
                'relationships': {
                    'organization': {
                        'data': {
                            'type': 'organizations',
                            'id': str(organization.id)
                        }
                    }
                }
            }
        }
        update_response = client.put(update_url, update_data, format='json')
        print(f"Update response content: {update_response.content}")  # Debug print
        assert update_response.status_code == 200
        assert update_response.data['data']['attributes']['name'] == update_data['data']['attributes']['name']
    
    def test_resource_delete_endpoint(self, api_client, test_resource):
        """Test that resource can be deleted via API"""
        url = reverse('rbac:resource-detail', kwargs={'pk': test_resource.id})
        response = api_client.delete(url)
        
        assert response.status_code == 204
        assert not Resource.objects.filter(id=test_resource.id).exists()
    
    def test_resource_grant_access_endpoint(self, client, test_resource, test_user):
        """Test that access can be granted to a resource via API"""
        client.force_authenticate(user=test_user)
        url = reverse('rbac:resource-grant-access', kwargs={'pk': test_resource.id})
        
        # Test with valid data
        data = {
            'user': test_user.id,
            'access_type': 'write'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 200
        assert response.data['data']['attributes']['message'] == f"Access granted to user {test_user.username}"
        assert test_resource.has_access(test_user, 'write') is True
        
        # Test with missing user
        data = {'access_type': 'write'}
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 400
        assert 'User and access type are required' in response.data['errors'][0]['detail']
        
        # Test with missing access_type
        data = {'user': test_user.id}
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 400
        assert 'User and access type are required' in response.data['errors'][0]['detail']
        
        # Test with invalid access_type
        data = {
            'user': test_user.id,
            'access_type': 'invalid'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 400
        assert 'Invalid access type' in response.data['errors'][0]['detail']
        
        # Test with non-existent user
        data = {
            'user': 99999,
            'access_type': 'write'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 404
        assert 'User not found' in response.data['errors'][0]['detail']
    
    def test_resource_revoke_access_endpoint(self, client, test_resource, test_user):
        """Test that access can be revoked from a resource via API"""
        client.force_authenticate(user=test_user)
        # First grant access
        test_resource.grant_access(test_user, 'write')
        url = reverse('rbac:resource-revoke-access', kwargs={'pk': test_resource.id})
        
        # Test with valid data (including access_type)
        data = {
            'user': test_user.id,
            'access_type': 'write'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 200
        assert response.data['data']['attributes']['message'] == f"Access revoked from user {test_user.username}"
        assert test_resource.has_access(test_user, 'write') is False
        
        # Test revoking all access types
        test_resource.grant_access(test_user, 'read')
        # No need to grant write access again since we're testing revoking all access types
        data = {'user': test_user.id}
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 200
        assert test_resource.has_access(test_user, 'read') is False
        assert test_resource.has_access(test_user, 'write') is False
        
        # Test with missing user
        data = {'access_type': 'write'}
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 400
        assert 'User is required' in response.data['errors'][0]['detail']
        
        # Test with invalid access_type
        data = {
            'user': test_user.id,
            'access_type': 'invalid'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 400
        assert 'Invalid access type' in response.data['errors'][0]['detail']
        
        # Test with non-existent user
        data = {
            'user': 99999,
            'access_type': 'write'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 404
        assert 'User not found' in response.data['errors'][0]['detail'] 