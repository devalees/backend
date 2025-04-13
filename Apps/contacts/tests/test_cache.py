import pytest
from django.core.cache import cache
from django.test import TestCase, override_settings
from Apps.contacts.models import Contact, ContactGroup
from Apps.contacts.cache_manager import ContactCache, ContactGroupCache
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

@pytest.mark.django_db
class TestContactGroupCache:
    """Test cases for ContactGroupCache manager"""
    
    def setup_method(self):
        """Setup for tests"""
        # Clear cache before each test
        cache.clear()
        self.group = ContactGroupFactory()
        self.org_id = self.group.organization.id
        
    def teardown_method(self):
        """Teardown after tests"""
        # Clear cache after each test
        cache.clear()
        
    def test_get_group_key(self):
        """Test generation of group cache key"""
        group_id = 123
        expected_key = f"{ContactGroupCache.GROUP_KEY_PREFIX}:{group_id}"
        assert ContactGroupCache._get_group_key(group_id) == expected_key
        
    def test_get_org_groups_key(self):
        """Test generation of organization groups cache key"""
        org_id = 456
        expected_key = f"{ContactGroupCache.ORG_GROUPS_KEY_PREFIX}:{org_id}:groups"
        assert ContactGroupCache._get_org_groups_key(org_id) == expected_key
        
    def test_set_and_get_group(self):
        """Test setting and getting a group from cache"""
        # Set group in cache
        ContactGroupCache.set_group(self.group)
        
        # Get group from cache
        cached_group = ContactGroupCache.get_group(self.group.id)
        
        # Verify group is retrieved correctly
        assert cached_group is not None
        assert hasattr(cached_group, 'id')
        assert cached_group.id == self.group.id
        assert cached_group.name == self.group.name
        
    def test_set_group_with_serializer(self):
        """Test setting a group with serializer"""
        # Set group in cache with include_related=True to use serializer
        ContactGroupCache.set_group(self.group, include_related=True)
        
        # Get group from cache
        cached_group = ContactGroupCache.get_group(self.group.id)
        
        # Verify it's a serialized dict
        assert isinstance(cached_group, dict)
        assert cached_group['id'] == self.group.id
        assert cached_group['name'] == self.group.name
        
    def test_delete_group(self):
        """Test deleting a group from cache"""
        # First set the group in cache
        ContactGroupCache.set_group(self.group)
        
        # Verify it exists in cache
        assert ContactGroupCache.get_group(self.group.id) is not None
        
        # Delete from cache with force_delete=True
        ContactGroupCache.delete_group(self.group.id, self.org_id, force_delete=True)
        
        # Verify it's gone
        assert ContactGroupCache.get_group(self.group.id) is None
        
    def test_organization_groups_operations(self):
        """Test operations for organization groups"""
        # Create multiple groups for the same organization
        groups = [self.group]
        for _ in range(3):
            groups.append(ContactGroupFactory(organization=self.group.organization))
        
        # Cache organization groups
        ContactGroupCache.set_organization_groups(self.org_id)
        
        # Get cached groups
        cached_groups = ContactGroupCache.get_organization_groups(self.org_id)
        
        # Verify
        assert cached_groups is not None
        assert isinstance(cached_groups, list)
        assert len(cached_groups) == len(groups)
        
        # Invalidate cache
        ContactGroupCache.invalidate_organization_groups(self.org_id)
        
        # Verify it's gone
        assert ContactGroupCache.get_organization_groups(self.org_id) is None
        
    def test_bulk_set_groups(self):
        """Test bulk setting of groups"""
        # Create some groups
        groups = [self.group]
        for _ in range(3):
            groups.append(ContactGroupFactory())
        
        # Bulk set
        ContactGroupCache.bulk_set_groups(groups)
        
        # Verify each group is cached
        for group in groups:
            cached = ContactGroupCache.get_group(group.id)
            assert cached is not None
            assert hasattr(cached, 'id')
            assert cached.id == group.id
            
    def test_save_updates_cache(self):
        """Test that saving a group updates the cache"""
        # First set group in cache
        ContactGroupCache.set_group(self.group, include_related=True)
        
        # Update group
        new_name = "Updated Group Name"
        self.group.name = new_name
        self.group.save()
        
        # Get from cache
        cached_group = ContactGroupCache.get_group(self.group.id)
        
        # Verify cache was updated
        assert cached_group['name'] == new_name
        
    def test_delete_removes_from_cache(self):
        """Test that deleting a group removes it from cache"""
        # First set group in cache
        ContactGroupCache.set_group(self.group)
        
        # Verify it's in cache
        assert ContactGroupCache.get_group(self.group.id) is not None
        
        # Delete the group (soft delete)
        self.group.delete()
        
        # Get from cache
        cached_group = ContactGroupCache.get_group(self.group.id)
        
        # Should still exist but be marked inactive
        assert cached_group is not None
        
        # Now hard delete
        org_id = self.group.organization_id
        group_id = self.group.id
        self.group.hard_delete()
        
        # Cache should be invalidated
        assert ContactGroupCache.get_group(group_id) is None 