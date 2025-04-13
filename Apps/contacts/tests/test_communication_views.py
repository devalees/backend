import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.cache import cache
from Apps.contacts.models import Communication, CommunicationTemplate, CommunicationMonitoring
from Apps.contacts.views import CommunicationViewSet, CommunicationTemplateViewSet, CommunicationMonitoringViewSet
from Apps.contacts.tests.factories import CommunicationFactory, ContactFactory, CommunicationMonitoringFactory
from Apps.contacts.cache_manager import CommunicationCache
from Apps.core.tests.factories import UserFactory
from Apps.entity.tests.factories import OrganizationFactory
from unittest.mock import patch, MagicMock
import json
from django.test import override_settings
from django.utils import timezone
import datetime

@pytest.mark.django_db
class TestCommunicationViewSet:
    """Test cases for CommunicationViewSet"""
    
    def setup_method(self):
        """Setup before each test"""
        self.user = UserFactory()
        self.factory = APIRequestFactory()
        self.contact = ContactFactory(created_by=self.user, updated_by=self.user)
        self.communication = CommunicationFactory(
            contact=self.contact,
            created_by=self.user,
            updated_by=self.user,
            organization=self.contact.organization
        )
        self.detail_url = reverse('communication-detail', kwargs={'pk': self.communication.id})
        self.list_url = reverse('communication-list')
        
        # Clear cache
        cache.clear()
        
    def teardown_method(self):
        """Teardown after each test"""
        cache.clear()
        
    def test_list_communications(self):
        """Test listing communications"""
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
    def test_list_communications_with_organization_filter(self):
        """Test listing communications with organization filter"""
        org_id = self.communication.organization.id
        url = f"{self.list_url}?organization={org_id}"
        
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Debug the response data
        print(f"\nResponse data type: {type(response.data)}")
        if hasattr(response.data, 'items'):
            print(f"Response data keys: {response.data.keys()}")
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        
        # Check that all communications are for the correct organization
        for item in data:
            if isinstance(item, dict):
                if isinstance(item.get('organization'), dict):
                    assert item['organization']['id'] == org_id
                else:
                    assert item['organization'] == org_id
            else:
                assert item.organization.id == org_id
                
    def test_list_communications_with_contact_filter(self):
        """Test listing communications with contact filter"""
        contact_id = self.communication.contact.id
        url = f"{self.list_url}?contact={contact_id}"
        
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        
        # Check that all communications are for the correct contact
        for item in data:
            if isinstance(item, dict):
                assert item['contact'] == contact_id
            else:
                assert item.contact.id == contact_id
    
    def test_list_communications_with_status_filter(self):
        """Test listing communications with status filter"""
        status_param = 'draft'
        url = f"{self.list_url}?status={status_param}"
        
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        
        # Check that all communications have the correct status
        for item in data:
            if isinstance(item, dict):
                assert item['status'] == status_param
            else:
                assert item.status == status_param
                
    def test_list_communications_uses_cache(self):
        """Test that communication listing uses cache"""
        org_id = self.communication.organization.id
        url = f"{self.list_url}?organization={org_id}"
        
        # Prepare cache with mock data to verify it's used
        mock_communications = [{
            'id': self.communication.id,
            'subject': 'Cached Communication',
            'contact': self.contact.id,
            'organization': org_id
        }]
        cache_key = CommunicationCache._get_org_communications_key(org_id)
        cache.set(cache_key, mock_communications)
        
        # Make request
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'list'})
        
        # Need to patch the CommunicationCache.get_organization_communications to return our mock
        with patch('Apps.contacts.cache_manager.CommunicationCache.get_organization_communications',
                   return_value=mock_communications):
            response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        # Should contain the cached subject
        assert 'Cached Communication' in str(response.data)
        
    def test_retrieve_communication(self):
        """Test retrieving a single communication"""
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.communication.id
        assert response.data['subject'] == self.communication.subject
        
        # Check that a monitoring record was created
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type='view'
        )
        assert records.count() == 1
        
    def test_retrieve_communication_uses_cache(self):
        """Test that communication retrieval uses cache when available"""
        # Cache the communication first
        CommunicationCache.set_communication(self.communication, include_related=True)
        
        # Make request
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'retrieve'})
        
        # Mock to verify cache is used
        mock_cached = {
            'id': self.communication.id,
            'subject': 'Cached Communication Subject',
            'message': self.communication.message,
            'contact': self.communication.contact.id,
            'organization': self.communication.organization.id
        }
        
        with patch('Apps.contacts.cache_manager.CommunicationCache.get_communication',
                   return_value=mock_cached):
            response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        # Should contain the mocked subject
        assert response.data['subject'] == 'Cached Communication Subject'
        
    def test_create_communication(self):
        """Test creating a communication"""
        data = {
            'subject': 'New Test Communication',
            'message': 'This is a test message',
            'communication_type': 'email',
            'status': 'draft',
            'contact': self.contact.id,
            'organization': self.contact.organization.id
        }
        
        request = self.factory.post(
            self.list_url, 
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'post': 'create'})
        response = view(request)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == data['subject']
        assert response.data['message'] == data['message']
        
        # Check that the communication was created in the database
        new_communication = Communication.objects.get(subject=data['subject'])
        assert new_communication.message == data['message']
        assert new_communication.created_by == self.user
        assert new_communication.updated_by == self.user
        
    def test_update_communication(self):
        """Test updating a communication"""
        data = {
            'subject': 'Updated Communication Subject',
            'message': 'Updated message content',
            'communication_type': 'email',
            'status': 'draft',
            'contact': self.contact.id,
            'organization': self.contact.organization.id
        }
        
        request = self.factory.put(
            self.detail_url, 
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == data['subject']
        assert response.data['message'] == data['message']
        
        # Check that the communication was updated in the database
        updated_communication = Communication.objects.get(id=self.communication.id)
        assert updated_communication.subject == data['subject']
        assert updated_communication.message == data['message']
        assert updated_communication.updated_by == self.user
        
        # Check that a monitoring record was created
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type='update'
        )
        assert records.count() >= 1  # Could be more due to save() in model
        
    def test_soft_delete_communication(self):
        """Test soft deleting a communication"""
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that the communication was soft deleted
        updated_comm = Communication.objects.get(id=self.communication.id)
        assert not updated_comm.is_active
        
        # Check that a monitoring record was created
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type='delete',
            description='Soft delete'
        )
        assert records.count() == 1
        
    def test_hard_delete_communication(self):
        """Test hard deleting a communication"""
        hard_delete_url = reverse('communication-hard-delete', kwargs={'pk': self.communication.id})
        
        request = self.factory.delete(hard_delete_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'delete': 'hard_delete'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that the communication was hard deleted
        assert not Communication.objects.filter(id=self.communication.id).exists()
        
        # Check that a monitoring record was created
        records = CommunicationMonitoring.objects.filter(
            communication=None,
            user=self.user,
            activity_type='delete',
            description='Hard delete'
        )
        assert records.count() == 1
        
    def test_refresh_cache_endpoint(self):
        """Test refreshing communication cache"""
        org_id = self.communication.organization.id
        cache_key = CommunicationCache._get_org_communications_key(org_id)
        
        # Clear any existing cache
        cache.delete(cache_key)
        
        # Make request to refresh cache
        url = f"{reverse('communication-refresh-cache')}?organization={org_id}"
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'refresh_cache'})
        
        # Mock to verify cache methods are called
        with patch('Apps.contacts.cache_manager.CommunicationCache.invalidate_organization_communications') as mock_invalidate, \
             patch('Apps.contacts.cache_manager.CommunicationCache.set_organization_communications') as mock_set:
            response = view(request)
            
            # Verify cache methods were called
            mock_invalidate.assert_called_once_with(org_id)
            mock_set.assert_called_once_with(org_id)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert str(org_id) in response.data['message']
        
    def test_refresh_cache_endpoint_missing_org(self):
        """Test refreshing cache without org param"""
        url = reverse('communication-refresh-cache')
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'get': 'refresh_cache'})
        response = view(request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        
    def test_send_communication_endpoint(self):
        """Test sending a communication"""
        send_url = reverse('communication-send', kwargs={'pk': self.communication.id})
        
        request = self.factory.post(send_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'post': 'send'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the communication status was updated
        updated_comm = Communication.objects.get(id=self.communication.id)
        assert updated_comm.status == 'sent'
        assert updated_comm.sent_at is not None
        
        # Check for monitoring records
        # There should be at least 2: one for transitioning to sending, one for transitioning to sent
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type__in=['send', 'update']
        )
        assert records.count() >= 2
        
    def test_schedule_communication_endpoint(self):
        """Test scheduling a communication"""
        schedule_url = reverse('communication-schedule', kwargs={'pk': self.communication.id})
        future_time = (timezone.now() + datetime.timedelta(hours=1)).isoformat()
        
        data = {
            'scheduled_at': future_time
        }
        
        request = self.factory.post(
            schedule_url,
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'post': 'schedule'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the communication status was updated
        updated_comm = Communication.objects.get(id=self.communication.id)
        assert updated_comm.status == 'scheduled'
        assert updated_comm.scheduled_at is not None
        
        # Check for a monitoring record
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type='schedule'
        )
        assert records.count() == 1
        
    def test_cancel_communication_endpoint(self):
        """Test canceling a communication"""
        # First schedule the communication
        self.communication.status = 'scheduled'
        self.communication.scheduled_at = timezone.now() + datetime.timedelta(hours=1)
        self.communication.save()
        
        cancel_url = reverse('communication-cancel', kwargs={'pk': self.communication.id})
        
        request = self.factory.post(cancel_url)
        force_authenticate(request, user=self.user)
        view = CommunicationViewSet.as_view({'post': 'cancel'})
        response = view(request, pk=self.communication.id)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that the communication status was updated
        updated_comm = Communication.objects.get(id=self.communication.id)
        assert updated_comm.status == 'cancelled'
        
        # Check for a monitoring record
        records = CommunicationMonitoring.objects.filter(
            communication=self.communication,
            user=self.user,
            activity_type='cancel'
        )
        assert records.count() == 1


@pytest.mark.django_db
class TestCommunicationTemplateViewSet:
    """Test cases for CommunicationTemplateViewSet"""
    
    def setup_method(self):
        """Setup before each test"""
        self.user = UserFactory()
        self.factory = APIRequestFactory()
        self.organization = OrganizationFactory()
        self.contact = ContactFactory(organization=self.organization)
        
        self.template = CommunicationTemplate.objects.create(
            name='Test Template',
            description='Test description',
            organization=self.organization,
            created_by=self.user,
            updated_by=self.user,
            subject_template='Hello {{contact.name}}',
            message_template='This is a test message for {{contact.name}}',
            communication_type='email'
        )
        
        self.detail_url = reverse('communicationtemplate-detail', kwargs={'pk': self.template.id})
        self.list_url = reverse('communicationtemplate-list')
        
    def test_list_templates(self):
        """Test listing templates"""
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
    def test_retrieve_template(self):
        """Test retrieving a single template"""
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.template.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.template.id
        assert response.data['name'] == self.template.name
        
    def test_create_template(self):
        """Test creating a template"""
        data = {
            'name': 'New Test Template',
            'description': 'New test description',
            'subject_template': 'Hello New {{contact.name}}',
            'message_template': 'This is a new test message for {{contact.name}}',
            'communication_type': 'email',
            'organization': self.organization.id
        }
        
        request = self.factory.post(
            self.list_url, 
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'post': 'create'})
        response = view(request)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert response.data['subject_template'] == data['subject_template']
        
        # Check that the template was created in the database
        new_template = CommunicationTemplate.objects.get(name=data['name'])
        assert new_template.subject_template == data['subject_template']
        assert new_template.created_by == self.user
        assert new_template.updated_by == self.user
        
    def test_update_template(self):
        """Test updating a template"""
        data = {
            'name': 'Updated Template Name',
            'description': 'Updated description',
            'subject_template': 'Updated subject for {{contact.name}}',
            'message_template': 'Updated message for {{contact.name}}',
            'communication_type': 'email',
            'organization': self.organization.id
        }
        
        request = self.factory.put(
            self.detail_url, 
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.template.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']
        assert response.data['description'] == data['description']
        
        # Check that the template was updated in the database
        updated_template = CommunicationTemplate.objects.get(id=self.template.id)
        assert updated_template.name == data['name']
        assert updated_template.description == data['description']
        assert updated_template.updated_by == self.user
        
    def test_soft_delete_template(self):
        """Test soft deleting a template"""
        request = self.factory.delete(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.template.id)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check that the template was soft deleted
        updated_template = CommunicationTemplate.objects.get(id=self.template.id)
        assert not updated_template.is_active
        
    def test_create_communication_from_template(self):
        """Test creating a communication from a template"""
        create_comm_url = reverse('communicationtemplate-create-communication', kwargs={'pk': self.template.id})
        
        data = {
            'contact': self.contact.id
        }
        
        request = self.factory.post(
            create_comm_url, 
            json.dumps(data),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        view = CommunicationTemplateViewSet.as_view({'post': 'create_communication'})
        response = view(request, pk=self.template.id)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that the communication was created with rendered template
        expected_subject = f"Hello {self.contact.name}"
        expected_message = f"This is a test message for {self.contact.name}"
        
        assert response.data['subject'] == expected_subject
        assert response.data['message'] == expected_message
        assert response.data['contact'] == self.contact.id
        assert response.data['communication_type'] == 'email'
        assert response.data['status'] == 'draft'


@pytest.mark.django_db
class TestCommunicationMonitoringViewSet:
    """Test cases for CommunicationMonitoringViewSet"""
    
    def setup_method(self):
        """Setup before each test"""
        self.user = UserFactory()
        self.factory = APIRequestFactory()
        self.organization = OrganizationFactory()
        self.contact = ContactFactory(organization=self.organization)
        self.communication = CommunicationFactory(
            contact=self.contact,
            organization=self.organization,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.activity = CommunicationMonitoringFactory(
            communication=self.communication,
            user=self.user,
            organization=self.organization,
            activity_type='view'
        )
        
        self.detail_url = reverse('communicationmonitoring-detail', kwargs={'pk': self.activity.id})
        self.list_url = reverse('communicationmonitoring-list')
        
    def test_list_activities(self):
        """Test listing monitoring activities"""
        request = self.factory.get(self.list_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        
    def test_retrieve_activity(self):
        """Test retrieving a single activity"""
        request = self.factory.get(self.detail_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.activity.id)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.activity.id
        assert response.data['activity_type'] == self.activity.activity_type
        
    def test_list_activities_with_filters(self):
        """Test filtering activities"""
        # Test organization filter
        org_url = f"{self.list_url}?organization={self.organization.id}"
        request = self.factory.get(org_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
            
        # Check each item is for the correct organization
        for item in data:
            # Check organization - could be ID or object
            if isinstance(item, dict):
                if isinstance(item.get('organization'), dict):
                    assert item['organization']['id'] == self.organization.id
                else:
                    assert item['organization'] == self.organization.id
            else:
                assert item.organization.id == self.organization.id
            
        # Test communication filter
        comm_url = f"{self.list_url}?communication={self.communication.id}"
        request = self.factory.get(comm_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
            
        # Check each item is for the correct communication
        for item in data:
            if isinstance(item, dict):
                if isinstance(item.get('communication'), dict):
                    assert item['communication']['id'] == self.communication.id
                else:
                    assert item['communication'] == self.communication.id
            else:
                assert item.communication.id == self.communication.id
            
        # Test user filter
        user_url = f"{self.list_url}?user={self.user.id}"
        request = self.factory.get(user_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
            
        # Check each item is for the correct user
        for item in data:
            if isinstance(item, dict):
                if isinstance(item.get('user'), dict):
                    assert item['user']['id'] == self.user.id
                else:
                    assert item['user'] == self.user.id
            else:
                assert item.user.id == self.user.id
            
        # Test activity_type filter
        type_url = f"{self.list_url}?activity_type=view"
        request = self.factory.get(type_url)
        force_authenticate(request, user=self.user)
        view = CommunicationMonitoringViewSet.as_view({'get': 'list'})
        response = view(request)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle pagination if present
        data = response.data
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
            
        # Check each item has the correct activity type
        for item in data:
            if isinstance(item, dict):
                assert item['activity_type'] == 'view'
            else:
                assert item.activity_type == 'view' 