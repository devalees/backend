import pytest
from django.test import RequestFactory
from Apps.contacts.models import Contact, ContactMonitoring
from Apps.contacts.tests.factories import ContactFactory, ContactMonitoringFactory
from Apps.entity.tests.factories import OrganizationFactory
from Apps.core.tests.factories import UserFactory
from unittest.mock import patch
from django.db import transaction

@pytest.mark.django_db
class TestContactMonitoring:
    """Test cases for ContactMonitoring model"""
    
    def test_create_monitoring_record(self):
        """Test creating a monitoring record directly"""
        contact = ContactFactory()
        record = ContactMonitoringFactory(contact=contact)
        assert record.id is not None
        assert record.contact is not None
        assert record.user is not None
        assert record.activity_type == 'view'
        assert record.organization == contact.organization

    def test_str_representation(self):
        """Test string representation of monitoring record"""
        contact = ContactFactory()
        record = ContactMonitoringFactory(contact=contact)
        # String should include activity type, contact name, and timestamp
        assert record.get_activity_type_display() in str(record)
        assert contact.name in str(record)
        
    def test_monitoring_on_contact_create(self):
        """Test monitoring record creation when contact is created"""
        user = UserFactory()
        organization = OrganizationFactory.create()  # Ensure organization is created
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        # Create contact with explicit organization and request metadata
        contact = Contact(
            name='Test Contact',
            email='test@example.com',
            phone='+1555123456',
            organization=organization,
            created_by=user,
            updated_by=user
        )
        contact.save(user=user, request_meta=request.META)
        
        # Verify monitoring record was created
        records = ContactMonitoring.objects.filter(
            contact=contact,
            activity_type='create'
        )
        assert records.count() >= 1, "No create monitoring records found"
        record = records.first()
        assert record.ip_address == '192.168.1.1'
        assert record.user_agent == 'Test Browser'
        
    def test_monitoring_on_contact_update(self):
        """Test monitoring record creation when contact is updated"""
        # First create a contact
        contact = ContactFactory()
        
        # Now update it
        user = UserFactory()
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.2'
        request.META['HTTP_USER_AGENT'] = 'Test Browser 2'
        
        contact.name = 'Updated Name'
        contact.save(user=user, request_meta=request.META)
        
        # Verify monitoring record was created
        records = ContactMonitoring.objects.filter(
            contact=contact,
            user=user,
            activity_type='update'
        )
        assert records.count() == 1
        record = records.first()
        assert record.ip_address == '192.168.1.2'
        assert record.user_agent == 'Test Browser 2'
        
    def test_monitoring_on_contact_soft_delete(self):
        """Test monitoring record creation on soft delete"""
        contact = ContactFactory()
        user = UserFactory()
        request_factory = RequestFactory()
        request = request_factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.3'
        
        # Soft delete
        contact.delete(user=user, request_meta=request.META)
        
        # Verify monitoring records
        records = ContactMonitoring.objects.filter(
            contact=contact,
            user=user,
            activity_type='delete'
        )
        assert records.count() == 1
        record = records.first()
        assert 'Soft delete' in record.description
        
    def test_monitoring_on_contact_hard_delete(self):
        """Test monitoring record creation on hard delete"""
        with transaction.atomic():
            contact = ContactFactory()
            contact_id = contact.id
            org_id = contact.organization.id
            user = UserFactory()
            request_factory = RequestFactory()
            request = request_factory.get('/')
            request.META['REMOTE_ADDR'] = '192.168.1.4'
            request.META['HTTP_USER_AGENT'] = 'Test Browser'
            
            # Create a monitoring record before deletion to verify records exist
            pre_delete_record = ContactMonitoring.log_activity(
                contact=contact,
                user=user,
                activity_type='view',
                description='Pre-delete view',
                ip_address='192.168.1.4',
                user_agent='Test Browser',
                metadata={'pre_delete': True}
            )
            
            print(f"\nPre-delete record created: {pre_delete_record.id}")
            
            # Hard delete
            contact.hard_delete(user=user, request_meta=request.META)
            
            # Debug: Print all monitoring records for this organization
            all_records = ContactMonitoring.objects.filter(organization_id=org_id).order_by('-created_at')
            print("\nAll monitoring records after hard delete:")
            for record in all_records:
                print(f"ID: {record.id}, Activity: {record.activity_type}, Description: {record.description}, Created: {record.created_at}")
            
            # Verify monitoring record was created (with organization-only query)
            records = ContactMonitoring.objects.filter(
                organization_id=org_id,
                activity_type='delete',
                description='Hard delete'
            ).order_by('-created_at')  # Get the most recent record
            
            assert records.exists(), "No delete monitoring records found"
            record = records.first()
            assert record.ip_address == '192.168.1.4'
            assert record.user_agent == 'Test Browser'
            assert record.metadata.get('method') == 'hard_delete'
        
    def test_activity_log_class_method(self):
        """Test the log_activity class method"""
        contact = ContactFactory()
        user = UserFactory()
        
        # Use the class method directly
        record = ContactMonitoring.log_activity(
            contact=contact,
            user=user,
            activity_type='view',
            description='Test description',
            ip_address='192.168.1.5',
            user_agent='Test Agent',
            metadata={'test_key': 'test_value'}
        )
        
        # Verify the record was created with the right attributes
        assert record.id is not None
        assert record.contact == contact
        assert record.user == user
        assert record.activity_type == 'view'
        assert record.description == 'Test description'
        assert record.ip_address == '192.168.1.5'
        assert record.user_agent == 'Test Agent'
        assert record.metadata == {'test_key': 'test_value'} 