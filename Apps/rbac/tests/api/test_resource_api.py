import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from Apps.rbac.models import Resource
from Apps.entity.models import Organization

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
            'name': 'Test Resource',
            'description': 'Test Description',
            'organization': test_organization.id,
            'resource_type': 'document'
        }
        response = client.post(url, data, content_type='application/json')
        assert response.status_code == 201
        assert response.data['data']['attributes']['name'] == data['name']
    
    def test_resource_retrieve_endpoint(self, api_client, test_resource):
        """Test that resource can be retrieved via API"""
        url = reverse('rbac:resource-detail', kwargs={'pk': test_resource.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['data']['attributes']['name'] == test_resource.name
    
    def test_resource_update_endpoint(self, client, test_organization, test_user):
        """Test that resource can be updated via API"""
        client.force_authenticate(user=test_user)
        # First create a resource
        create_url = reverse('rbac:resource-list')
        create_data = {
            'data': {
                'type': 'resources',
                'attributes': {
                    'name': 'Original Resource',
                    'description': 'Original Description',
                    'resource_type': 'document',
                    'organization': test_organization.id,
                    'is_active': True
                }
            }
        }
        create_response = client.post(create_url, create_data, format='json')
        assert create_response.status_code == 201
        resource_id = create_response.data['data']['id']

        # Now update it
        url = reverse('rbac:resource-detail', kwargs={'pk': resource_id})
        update_data = {
            'data': {
                'type': 'resources',
                'id': str(resource_id),
                'attributes': {
                    'name': 'Updated Resource',
                    'description': 'Updated Description',
                    'resource_type': 'document',
                    'organization': test_organization.id,
                    'is_active': True
                }
            }
        }
        response = client.put(url, update_data, format='json')
        assert response.status_code == 200
        assert response.data['data']['attributes']['name'] == 'Updated Resource'
    
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