import pytest
from django.core.cache import cache
from django.test import TestCase, override_settings
from Apps.contacts.models import ContactList, Contact
from Apps.contacts.cache_manager import ContactListCache
from Apps.contacts.tests.factories import ContactListFactory, ContactFactory
from Apps.contacts.serializers import ContactListSerializer
from unittest.mock import patch, MagicMock
import pprint

@pytest.mark.django_db
class TestContactListCache:
    """Test cases for ContactListCache manager"""

    def setup_method(self):
        """Setup for tests"""
        # Clear cache before each test
        cache.clear()
        self.contact_list = ContactListFactory()
        self.org_id = self.contact_list.organization.id

    def teardown_method(self):
        """Teardown after tests"""
        # Clear cache after each test
        cache.clear()

    def test_get_list_key(self):
        """Test generation of contact list cache key"""
        list_id = 123
        expected_key = f"{ContactListCache.LIST_KEY_PREFIX}:{list_id}"
        assert ContactListCache._get_list_key(list_id) == expected_key

    def test_get_org_lists_key(self):
        """Test generation of organization lists cache key"""
        org_id = 456
        expected_key = f"{ContactListCache.ORG_LISTS_KEY_PREFIX}:{org_id}:lists"
        assert ContactListCache._get_org_lists_key(org_id) == expected_key
    
    def test_set_and_get_list(self):
        """Test setting and getting a contact list from cache"""
        # Set contact list in cache
        ContactListCache.set_list(self.contact_list)
        
        # Get contact list from cache
        cached_list = ContactListCache.get_list(self.contact_list.id)
        
        # Verify contact list is retrieved correctly
        assert cached_list is not None
        # Since we're using the default serialization in the test
        assert hasattr(cached_list, 'id')
        assert cached_list.id == self.contact_list.id
    
    def test_set_list_with_serializer(self):
        """Test setting a contact list with serializer"""
        # Clear any existing contacts from the factory-created list
        self.contact_list.contacts.clear()
        
        # Create a contact and add it to the list
        contact = ContactFactory(organization=self.contact_list.organization)
        self.contact_list.contacts.add(contact)
        
        # Print the count before caching
        print(f"\nBefore caching: Contact list has {self.contact_list.contacts.count()} contacts")
        
        # Set contact list in cache with serializer
        ContactListCache.set_list(self.contact_list, include_related=True)
        
        # Get contact list from cache
        cached_list = ContactListCache.get_list(self.contact_list.id)
        
        # Debug output to see what's in the contacts attribute
        print("DEBUG: cached_list.contacts type:", type(cached_list.contacts))
        if hasattr(cached_list.contacts, "__len__"):
            print("DEBUG: cached_list.contacts length:", len(cached_list.contacts))
        
        # If cached_list.contacts is a list, print its contents
        if isinstance(cached_list.contacts, list):
            print("DEBUG: cached_list.contacts content:", pprint.pformat(cached_list.contacts))
        elif hasattr(cached_list.contacts, "all"):
            # If it's a QuerySet or RelatedManager
            print("DEBUG: cached_list.contacts count:", cached_list.contacts.count())
        
        # Verify contact list is retrieved correctly with related data
        assert cached_list is not None
        assert hasattr(cached_list, 'contacts')
        # The test expects exactly 1 contact in the list
        assert len(cached_list.contacts) == 1
        assert cached_list.contacts[0].id == contact.id
    
    def test_delete_list(self):
        """Test deleting a contact list from cache"""
        # Set contact list in cache
        ContactListCache.set_list(self.contact_list)
        
        # Delete contact list from cache
        ContactListCache.delete_list(self.contact_list.id, self.org_id)
        
        # Verify contact list is not in cache
        assert ContactListCache.get_list(self.contact_list.id) is None
        
        # Verify organization lists are invalidated
        assert ContactListCache.get_organization_lists(self.org_id) is None
    
    def test_organization_lists_operations(self):
        """Test operations for organization contact lists"""
        # Create multiple contact lists for the organization
        list1 = self.contact_list
        list2 = ContactListFactory(organization=list1.organization)
        list3 = ContactListFactory(organization=list1.organization)
        
        # Set organization lists in cache
        ContactListCache.set_organization_lists(self.org_id)
        
        # Get organization lists from cache
        cached_lists = ContactListCache.get_organization_lists(self.org_id)
        
        # Verify lists are retrieved correctly
        assert cached_lists is not None
        assert len(cached_lists) == 3
        list_ids = [l.id for l in cached_lists]
        assert list1.id in list_ids
        assert list2.id in list_ids
        assert list3.id in list_ids
        
        # Invalidate organization lists
        ContactListCache.invalidate_organization_lists(self.org_id)
        
        # Verify organization lists are not in cache
        assert ContactListCache.get_organization_lists(self.org_id) is None
    
    def test_bulk_set_lists(self):
        """Test bulk setting contact lists in cache"""
        # Create multiple contact lists
        list1 = self.contact_list
        list2 = ContactListFactory(organization=list1.organization)
        list3 = ContactListFactory(organization=list1.organization)
        lists = [list1, list2, list3]
        
        # Bulk set lists in cache
        ContactListCache.bulk_set_lists(lists)
        
        # Verify lists are in cache
        for list_obj in lists:
            cached_list = ContactListCache.get_list(list_obj.id)
            assert cached_list is not None
            assert cached_list.id == list_obj.id
    
    @patch('Apps.contacts.cache_manager.cache')
    def test_cache_ttl(self, mock_cache):
        """Test cache TTL setting"""
        # Set contact list in cache with custom TTL
        ttl = 7200  # 2 hours
        ContactListCache.set_list(self.contact_list, ttl=ttl)
        
        # Verify cache.set was called with correct TTL
        mock_cache.set.assert_called_with(
            ContactListCache._get_list_key(self.contact_list.id),
            self.contact_list,  # The actual data being cached
            timeout=ttl
        )
    
    def test_save_updates_cache(self):
        """Test that saving a contact list updates the cache"""
        # Set contact list in cache
        ContactListCache.set_list(self.contact_list)
        
        # Update contact list
        self.contact_list.name = "Updated Name"
        self.contact_list.save()
        
        # Verify cache is updated
        cached_list = ContactListCache.get_list(self.contact_list.id)
        assert cached_list is not None
        assert cached_list.name == "Updated Name"
    
    def test_delete_removes_from_cache(self):
        """Test that deleting a contact list removes it from cache"""
        # Set contact list in cache
        ContactListCache.set_list(self.contact_list)
        
        # Delete contact list
        self.contact_list.delete()
        
        # Verify contact list is not in cache
        assert ContactListCache.get_list(self.contact_list.id) is None
        
        # Verify organization lists are invalidated
        assert ContactListCache.get_organization_lists(self.org_id) is None 