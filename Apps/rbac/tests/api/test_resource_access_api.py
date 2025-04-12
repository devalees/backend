import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from Apps.rbac.models import Resource, ResourceAccess
from Apps.entity.models import Organization

User = get_user_model()

@pytest.fixture
def test_resource(organization):
    """Create a test resource"""
    return Resource.objects.create(
        name="Test Resource",
        resource_type="document",
        organization=organization
    )

@pytest.fixture
def test_resource_access(test_resource, user, organization):
    """Create a test resource access"""
    return ResourceAccess.objects.create(
        resource=test_resource,
        user=user,
        access_type="read",
        organization=organization
    )

@pytest.mark.django_db
class TestResourceAccessAPI:
    """Test suite for ResourceAccess API endpoints"""
    
    def test_resource_access_list_endpoint(self, api_client, test_resource_access):
        """Test that resource access list endpoint returns correct data"""
        url = reverse('rbac:resourceaccess-list')
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['access_type'] == test_resource_access.access_type
    
    def test_resource_access_create_endpoint(self, api_client, test_resource, user, organization):
        """Test that resource access can be created via API"""
        url = reverse('rbac:resourceaccess-list')
        data = {
            'resource': test_resource.id,
            'user': user.id,
            'access_type': 'write',
            'organization': organization.id
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == 201
        assert ResourceAccess.objects.filter(
            resource=test_resource,
            user=user,
            access_type='write'
        ).exists()
    
    def test_resource_access_retrieve_endpoint(self, api_client, test_resource_access):
        """Test that resource access can be retrieved via API"""
        url = reverse('rbac:resourceaccess-detail', kwargs={'pk': test_resource_access.id})
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['data']['attributes']['access_type'] == test_resource_access.access_type
    
    def test_resource_access_update_endpoint(self, api_client, test_resource_access):
        """Test that resource access can be updated via API"""
        url = reverse('rbac:resourceaccess-detail', kwargs={'pk': test_resource_access.id})
        data = {
            'access_type': 'admin',
            'notes': 'Updated notes'
        }
        
        response = api_client.patch(url, data)
        
        assert response.status_code == 200
        test_resource_access.refresh_from_db()
        assert test_resource_access.access_type == 'admin'
        assert test_resource_access.notes == 'Updated notes'
    
    def test_resource_access_delete_endpoint(self, api_client, test_resource_access):
        """Test that resource access can be deleted via API"""
        url = reverse('rbac:resourceaccess-detail', kwargs={'pk': test_resource_access.id})
        response = api_client.delete(url)
        
        assert response.status_code == 204
        assert not ResourceAccess.objects.filter(id=test_resource_access.id).exists()
    
    def test_resource_access_activate_endpoint(self, api_client, test_resource_access):
        """Test that resource access can be activated via API"""
        # First deactivate the resource access
        test_resource_access.deactivate()
        test_resource_access.save()
        
        url = reverse('rbac:resourceaccess-activate', kwargs={'pk': test_resource_access.id})
        response = api_client.post(url)
        
        assert response.status_code == 200
        test_resource_access.refresh_from_db()
        assert test_resource_access.is_active is True
    
    def test_resource_access_deactivate_endpoint(self, api_client, test_resource_access):
        """Test that resource access can be deactivated via API"""
        url = reverse('rbac:resourceaccess-deactivate', kwargs={'pk': test_resource_access.id})
        response = api_client.post(url)
        
        assert response.status_code == 200
        test_resource_access.refresh_from_db()
        assert test_resource_access.is_active is False 