import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.cache import cache
from Apps.contacts.models import ContactList, Contact
from Apps.contacts.views import ContactListViewSet
from Apps.contacts.tests.factories import ContactFactory, ContactListFactory, OrganizationFactory
from Apps.core.tests.factories import UserFactory
from Apps.entity.tests.factories import TeamMemberFactory, TeamFactory, DepartmentFactory
from unittest.mock import patch, MagicMock
import json

@pytest.mark.django_db
class TestContactListViewSet:
    """Test cases for ContactListViewSet"""
    
    def setup_method(self):
        """Setup before each test"""
        self.user = UserFactory()
        self.factory = APIRequestFactory()
        # Create an organization and associate it with the user
        self.organization = OrganizationFactory()
        
        # Create department and team in this organization
        self.department = DepartmentFactory(organization=self.organization)
        self.team = TeamFactory(department=self.department)
        
        # Create team membership to properly associate user with the organization
        self.team_member = TeamMemberFactory(
            user=self.user,
            team=self.team,
            is_active=True
        )
        
        # Create contact list with the user and organization
        self.contact_list = ContactListFactory(
            created_by=self.user, 
            updated_by=self.user,
            organization=self.organization
        )
        self.detail_url = reverse('contactlist-detail', kwargs={'pk': self.contact_list.id})
        self.list_url = reverse('contactlist-list')
        
        # Clear cache
        cache.clear()
        
    def teardown_method(self):
        """Teardown after each test"""
        cache.clear()
        
    def test_list_contact_lists(self):
        """Test listing contact lists"""
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
    def test_list_contact_lists_with_organization_filter(self):
        """Test listing contact lists with organization filter"""
        org_id = self.contact_list.organization.id
        url = f"{self.list_url}?organization={org_id}"
        
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle potential pagination
        response_data = response.data
        results = response_data.get('results', response_data)
        
        assert len(results) >= 1
        # Check all contact lists belong to the specified organization
        if isinstance(results, list):
            for item in results:
                assert item['organization'] == org_id
        
    def test_retrieve_contact_list(self):
        """Test retrieving a contact list"""
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.contact_list.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.contact_list.id
        assert response.data['name'] == self.contact_list.name
        assert response.data['organization'] == self.contact_list.organization.id
        
    def test_create_contact_list(self):
        """Test creating a contact list"""
        org = OrganizationFactory()
        data = {
            'name': 'New Contact List',
            'description': 'A new contact list for testing',
            'organization': org.id,
            'is_active': True
        }
        
        request = self.factory.post(self.list_url, data, format='json')
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'post': 'create'})
        response = view(request)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert response.data['description'] == data['description']
        assert response.data['organization'] == org.id
        assert response.data['is_active'] == data['is_active']
        assert response.data['created_by'] == self.user.id
        
    def test_create_contact_list_with_contacts(self):
        """Test creating a contact list with contacts"""
        org = OrganizationFactory()
        contacts = [ContactFactory(organization=org) for _ in range(3)]
        contact_ids = [contact.id for contact in contacts]
        
        data = {
            'name': 'New Contact List with Contacts',
            'description': 'A new contact list with contacts for testing',
            'organization': org.id,
            'is_active': True,
            'contact_ids': contact_ids
        }
        
        request = self.factory.post(self.list_url, data, format='json')
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'post': 'create'})
        response = view(request)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert len(response.data['contacts']) == len(contacts)
        
    def test_update_contact_list(self):
        """Test updating a contact list"""
        data = {
            'name': 'Updated Contact List',
            'description': 'An updated contact list for testing'
        }
        
        request = self.factory.patch(self.detail_url, data, format='json')
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=self.contact_list.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']
        assert response.data['description'] == data['description']
        assert response.data['updated_by'] == self.user.id
        
    def test_update_contact_list_contacts(self):
        """Test updating contacts in a contact list"""
        org = self.contact_list.organization
        contacts = [ContactFactory(organization=org) for _ in range(3)]
        contact_ids = [contact.id for contact in contacts]
        
        data = {
            'contact_ids': contact_ids
        }
        
        request = self.factory.patch(self.detail_url, data, format='json')
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=self.contact_list.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['contacts']) == len(contacts)
        
    def test_soft_delete_contact_list(self):
        """Test soft deleting a contact list"""
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.contact_list.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the contact list is soft deleted
        self.contact_list.refresh_from_db()
        assert not self.contact_list.is_active
        
    def test_hard_delete_contact_list(self):
        """Test hard deleting a contact list"""
        # Use the correct URL format for actions
        hard_delete_url = reverse('contactlist-hard-delete', kwargs={'pk': self.contact_list.id})
        
        request = self.factory.delete(hard_delete_url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'delete': 'hard_delete'})
        response = view(request, pk=self.contact_list.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify the contact list is hard deleted
        assert not ContactList.objects.filter(id=self.contact_list.id).exists()
        
    def test_unauthorized_access(self):
        """Test unauthorized access to contact list endpoints"""
        # Test list endpoint
        request = self.factory.get(self.list_url)
        view = ContactListViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test detail endpoint
        request = self.factory.get(self.detail_url)
        view = ContactListViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.contact_list.id)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test create endpoint
        data = {'name': 'Unauthorized List'}
        request = self.factory.post(self.list_url, data, format='json')
        view = ContactListViewSet.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_organization_filtering(self):
        """Test that users can only access contact lists from their organization"""
        # Create a user in a different organization
        other_org = OrganizationFactory()
        other_user = UserFactory()
        
        # Create a department and team in this other organization
        other_department = DepartmentFactory(organization=other_org)
        other_team = TeamFactory(department=other_department)
        
        # Create team membership to properly associate other_user with the other organization
        other_team_member = TeamMemberFactory(
            user=other_user,
            team=other_team,
            is_active=True
        )
        
        # Create a contact list in this other organization
        other_list = ContactListFactory(organization=other_org, created_by=other_user)
        
        # The main test user should not have access to this list
        other_detail_url = reverse('contactlist-detail', kwargs={'pk': other_list.id})
        request = self.factory.get(other_detail_url)
        force_authenticate(request, user=self.user)
        view = ContactListViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=other_list.id)
        
        # Should return 404 as the user doesn't have access to this organization's contact list
        assert response.status_code == status.HTTP_404_NOT_FOUND 