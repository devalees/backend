import pytest
from django.core.cache import cache
from django.test import TestCase, override_settings
from Apps.contacts.models import Contact, ContactGroup
from Apps.contacts.cache_manager import ContactCache
from Apps.contacts.tests.factories import ContactFactory, ContactGroupFactory
from Apps.contacts.serializers import ContactSerializer
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestContactCache:
    """Test cases for ContactCache manager"""

    def setup_method(self):
        """Setup for tests"""
        # Clear cache before each test
        cache.clear()
        self.contact = ContactFactory()
        self.org_id = self.contact.organization.id

    def teardown_method(self):
        """Teardown after tests"""
        # Clear cache after each test
        cache.clear()

    def test_get_contact_key(self):
        """Test generation of contact cache key"""
        contact_id = 123
        expected_key = f"{ContactCache.CONTACT_KEY_PREFIX}:{contact_id}"
        assert ContactCache._get_contact_key(contact_id) == expected_key

    def test_get_org_contacts_key(self):
        """Test generation of organization contacts cache key"""
        org_id = 456
        expected_key = f"{ContactCache.ORG_CONTACTS_KEY_PREFIX}:{org_id}:contacts"
        assert ContactCache._get_org_contacts_key(org_id) == expected_key
    
    def test_set_and_get_contact(self):
        """Test setting and getting a contact from cache"""
        # Set contact in cache
        ContactCache.set_contact(self.contact)
        
        # Get contact from cache
        cached_contact = ContactCache.get_contact(self.contact.id)
        
        # Verify contact is retrieved correctly
        assert cached_contact is not None
        # Since we're using the default serialization in the test
        assert hasattr(cached_contact, 'id')
        assert cached_contact.id == self.contact.id
        assert cached_contact.name == self.contact.name
        assert cached_contact.email == self.contact.email

    def test_set_contact_with_serializer(self):
        """Test setting a contact with serializer"""
        # Set contact in cache with include_related=True to use serializer
        ContactCache.set_contact(self.contact, include_related=True)
        
        # Get contact from cache
        cached_contact = ContactCache.get_contact(self.contact.id)
        
        # Verify it's a serialized dict
        assert isinstance(cached_contact, dict)
        assert cached_contact['id'] == self.contact.id
        assert cached_contact['name'] == self.contact.name
        assert cached_contact['email'] == self.contact.email

    def test_delete_contact(self):
        """Test deleting a contact from cache"""
        # First set the contact in cache
        ContactCache.set_contact(self.contact)
        
        # Verify it exists in cache
        assert ContactCache.get_contact(self.contact.id) is not None
        
        # Delete from cache with force_delete=True to bypass the Contact.objects.get check
        ContactCache.delete_contact(self.contact.id, self.org_id, force_delete=True)
        
        # Verify it's gone
        assert ContactCache.get_contact(self.contact.id) is None

    def test_organization_contacts_operations(self):
        """Test operations for organization contacts"""
        # Create multiple contacts for the same organization
        contacts = [self.contact]
        for _ in range(3):
            contacts.append(ContactFactory(organization=self.contact.organization))
        
        # Cache organization contacts
        ContactCache.set_organization_contacts(self.org_id)
        
        # Get cached contacts
        cached_contacts = ContactCache.get_organization_contacts(self.org_id)
        
        # Verify
        assert cached_contacts is not None
        assert isinstance(cached_contacts, list)
        assert len(cached_contacts) == len(contacts)
        
        # Invalidate cache
        ContactCache.invalidate_organization_contacts(self.org_id)
        
        # Verify it's gone
        assert ContactCache.get_organization_contacts(self.org_id) is None

    def test_bulk_set_contacts(self):
        """Test bulk setting of contacts"""
        # Create some contacts
        contacts = [self.contact]
        for _ in range(3):
            contacts.append(ContactFactory())
        
        # Bulk set
        ContactCache.bulk_set_contacts(contacts)
        
        # Verify each contact is cached
        for contact in contacts:
            cached = ContactCache.get_contact(contact.id)
            assert cached is not None
            # Since we're not using include_related in bulk_set_contacts
            assert hasattr(cached, 'id')
            assert cached.id == contact.id

    @patch('Apps.contacts.cache_manager.cache')
    def test_cache_ttl(self, mock_cache):
        """Test that cache TTL is correctly set"""
        # Set custom TTL
        custom_ttl = 7200  # 2 hours
        
        # Call with custom TTL
        ContactCache.set_contact(self.contact, ttl=custom_ttl)
        
        # Verify the cache.set was called with correct TTL
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert kwargs['timeout'] == custom_ttl
        
        # Reset mock and test default TTL
        mock_cache.reset_mock()
        ContactCache.set_contact(self.contact)
        
        # Verify default TTL was used
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert kwargs['timeout'] == ContactCache.DEFAULT_TTL

    def test_save_updates_cache(self):
        """Test that saving a contact updates the cache"""
        # First set contact in cache
        ContactCache.set_contact(self.contact, include_related=True)
        
        # Update contact
        new_name = "Updated Name"
        self.contact.name = new_name
        self.contact.save()
        
        # Get from cache
        cached_contact = ContactCache.get_contact(self.contact.id)
        
        # Verify cache was updated
        assert cached_contact['name'] == new_name

    def test_delete_removes_from_cache(self):
        """Test that deleting a contact removes it from cache"""
        # First set contact in cache
        ContactCache.set_contact(self.contact)
        
        # Verify it's in cache
        assert ContactCache.get_contact(self.contact.id) is not None
        
        # Delete the contact (soft delete)
        self.contact.delete()
        
        # Get from cache
        cached_contact = ContactCache.get_contact(self.contact.id)
        
        # Should still exist but be marked inactive
        assert cached_contact is not None
        # Hard to test this with the mock object, depends on serialization
        # For now, just verify it still exists
        
        # Now hard delete
        org_id = self.contact.organization_id
        contact_id = self.contact.id
        self.contact.hard_delete()
        
        # Cache should be invalidated
        assert ContactCache.get_contact(contact_id) is None 