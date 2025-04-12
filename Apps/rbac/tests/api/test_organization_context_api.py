import pytest
import json
from django.urls import reverse
from rest_framework import status
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization

@pytest.mark.django_db
class TestOrganizationContextAPI:
    """Tests for the OrganizationContext API endpoints"""
    
    def test_list_organization_contexts(self, api_client, organization, organization_context):
        """Test listing organization contexts"""
        url = reverse('rbac:organizationcontext-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == organization_context.name
    
    def test_retrieve_organization_context(self, api_client, organization, organization_context):
        """Test retrieving a single organization context"""
        url = reverse('rbac:organizationcontext-detail', args=[organization_context.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['attributes']['name'] == organization_context.name
        assert response.data['data']['attributes']['description'] == organization_context.description
    
    def test_create_organization_context(self, api_client, organization):
        """Test creating a new organization context"""
        url = reverse('rbac:organizationcontext-list')
        data = {
            'data': {
                'type': 'organization_contexts',
                'attributes': {
                    'name': 'New Context',
                    'description': 'A new organization context'
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
        
        response = api_client.post(url, data=json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'data' in response.data
        assert response.data['data']['attributes']['name'] == 'New Context'
        assert response.data['data']['attributes']['description'] == 'A new organization context'
        
        # Verify it was created in the database
        assert OrganizationContext.objects.filter(name='New Context').exists()
    
    def test_update_organization_context(self, api_client, organization, organization_context):
        """Test updating an organization context"""
        url = reverse('rbac:organizationcontext-detail', args=[organization_context.id])
        data = {
            'data': {
                'type': 'organization_contexts',
                'id': str(organization_context.id),
                'attributes': {
                    'name': 'Updated Context',
                    'description': 'An updated organization context'
                }
            }
        }
        
        response = api_client.patch(url, data=json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['attributes']['name'] == 'Updated Context'
        assert response.data['data']['attributes']['description'] == 'An updated organization context'
        
        # Verify it was updated in the database
        organization_context.refresh_from_db()
        assert organization_context.name == 'Updated Context'
        assert organization_context.description == 'An updated organization context'
    
    def test_delete_organization_context(self, api_client, organization, organization_context):
        """Test deleting an organization context"""
        url = reverse('rbac:organizationcontext-detail', args=[organization_context.id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it was soft deleted in the database
        organization_context.refresh_from_db()
        assert organization_context.is_active is False
    
    def test_activate_organization_context(self, api_client, organization, organization_context):
        """Test activating an organization context"""
        # First deactivate it
        organization_context.deactivate()
        assert organization_context.is_active is False
        
        url = reverse('rbac:organizationcontext-activate', args=[organization_context.id])
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['attributes']['message'] == 'Organization context activated'
        
        # Verify it was activated in the database
        organization_context.refresh_from_db()
        assert organization_context.is_active is True
        assert organization_context.deactivated_at is None
    
    def test_deactivate_organization_context(self, api_client, organization, organization_context):
        """Test deactivating an organization context"""
        url = reverse('rbac:organizationcontext-deactivate', args=[organization_context.id])
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['attributes']['message'] == 'Organization context deactivated'
        
        # Verify it was deactivated in the database
        organization_context.refresh_from_db()
        assert organization_context.is_active is False
        assert organization_context.deactivated_at is not None
    
    def test_get_ancestors(self, api_client, organization, parent_organization_context, child_organization_context):
        """Test getting ancestors of an organization context"""
        url = reverse('rbac:organizationcontext-ancestors', args=[child_organization_context.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == parent_organization_context.name
    
    def test_get_descendants(self, api_client, organization, parent_organization_context, child_organization_context):
        """Test getting descendants of an organization context"""
        url = reverse('rbac:organizationcontext-descendants', args=[parent_organization_context.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == child_organization_context.name
    
    def test_get_children(self, api_client, organization, parent_organization_context, child_organization_context):
        """Test getting direct children of an organization context"""
        url = reverse('rbac:organizationcontext-children', args=[parent_organization_context.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == child_organization_context.name
    
    def test_get_parents(self, api_client, organization, parent_organization_context, child_organization_context):
        """Test getting all parents of an organization context"""
        url = reverse('rbac:organizationcontext-parents', args=[child_organization_context.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['attributes']['name'] == parent_organization_context.name
    
    def test_validation_duplicate_name(self, api_client, organization):
        """Test validation for duplicate names within the same organization"""
        # Create a context first
        OrganizationContext.objects.create(
            organization=organization,
            name='Duplicate Name',
            description='First context'
        )
        
        # Try to create another context with the same name
        url = reverse('rbac:organizationcontext-list')
        data = {
            'data': {
                'type': 'organization_contexts',
                'attributes': {
                    'name': 'Duplicate Name',
                    'description': 'Second context'
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
        
        response = api_client.post(url, data=json.dumps(data), content_type='application/json')
        
        print("Response data:", response.data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert any('name' in error['source']['pointer'] for error in response.data['errors'])
    
    def test_validation_parent_organization(self, api_client, organization, test_organization):
        """Test validation for parent belonging to the same organization"""
        # Create a context in a different organization
        other_context = OrganizationContext.objects.create(
            organization=test_organization,
            name='Other Context',
            description='Context in other organization'
        )
        
        # Try to create a context with a parent from a different organization
        url = reverse('rbac:organizationcontext-list')
        data = {
            'data': {
                'type': 'organization_contexts',
                'attributes': {
                    'name': 'New Context',
                    'description': 'A new context'
                },
                'relationships': {
                    'organization': {
                        'data': {
                            'type': 'organizations',
                            'id': str(organization.id)
                        }
                    },
                    'parent': {
                        'data': {
                            'type': 'organization_contexts',
                            'id': str(other_context.id)
                        }
                    }
                }
            }
        }
        
        response = api_client.post(url, data=json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert any('parent' in error['source']['pointer'] for error in response.data['errors'])
    
    def test_validation_circular_reference(self, api_client, organization, parent_organization_context, child_organization_context):
        """Test validation for circular references in parent-child relationships"""
        url = reverse('rbac:organizationcontext-detail', args=[parent_organization_context.id])
        data = {
            'data': {
                'type': 'organization_contexts',
                'id': str(parent_organization_context.id),
                'relationships': {
                    'parent': {
                        'data': {
                            'type': 'organization_contexts',
                            'id': str(child_organization_context.id)
                        }
                    }
                }
            }
        }
        
        response = api_client.patch(url, data=json.dumps(data), content_type='application/json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert any('parent' in error['source']['pointer'] for error in response.data['errors']) 