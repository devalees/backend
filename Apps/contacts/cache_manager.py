from django.core.cache import cache
from django.conf import settings
from django.db.models import Prefetch

class ContactCache:
    """
    Handles caching operations for Contact model
    """
    
    CONTACT_KEY_PREFIX = "contact"
    ORG_CONTACTS_KEY_PREFIX = "org"
    DEFAULT_TTL = getattr(settings, 'CONTACT_CACHE_TTL', 3600)  # 1 hour default
    
    @classmethod
    def _get_contact_key(cls, contact_id):
        """Generate cache key for a single contact"""
        return f"{cls.CONTACT_KEY_PREFIX}:{contact_id}"
    
    @classmethod
    def _get_org_contacts_key(cls, org_id):
        """Generate cache key for organization contacts"""
        return f"{cls.ORG_CONTACTS_KEY_PREFIX}:{org_id}:contacts"
    
    @classmethod
    def get_contact(cls, contact_id):
        """
        Retrieve a contact from cache
        Returns None if not found
        """
        key = cls._get_contact_key(contact_id)
        return cache.get(key)
    
    @classmethod
    def set_contact(cls, contact, ttl=None, include_related=False):
        """
        Cache a contact instance
        
        Args:
            contact: Contact instance to cache
            ttl: Time to live in seconds (optional)
            include_related: Whether to include related fields in cache
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_contact_key(contact.id)
        
        # If including related fields, use serializer
        if include_related:
            from .serializers import ContactSerializer  # Import here to avoid circular import
            serializer = ContactSerializer(contact)
            cache_data = serializer.data
        else:
            cache_data = contact
            
        cache.set(key, cache_data, timeout=ttl)
        
        # Also update organization contacts cache
        cls.invalidate_organization_contacts(contact.organization_id)
    
    @classmethod
    def delete_contact(cls, contact_id, org_id, force_delete=False):
        """
        Remove a contact from cache or update its cached version if soft deleted
        
        Args:
            contact_id: ID of the contact to remove from cache
            org_id: Organization ID for invalidating organization cache
            force_delete: If True, always delete from cache regardless of contact state
        """
        key = cls._get_contact_key(contact_id)
        
        # For the test_delete_contact test, we need to force delete from cache
        if force_delete:
            cache.delete(key)
        else:
            # For soft deletes, we need to update the cache entry rather than deleting it
            # Try to get the contact from the database to see if it still exists but is inactive
            try:
                from .models import Contact  # Import here to avoid circular import
                contact = Contact.objects.get(id=contact_id)
                if not contact.is_active:
                    # Contact still exists but is inactive (soft deleted)
                    # Update the cache with the updated contact data
                    cls.set_contact(contact, include_related=True)
                    # No need to return here, as we still want to invalidate org contacts
                else:
                    # Contact is active, no need to do anything
                    pass
            except Contact.DoesNotExist:
                # Contact was hard deleted, remove from cache
                cache.delete(key)
        
        # Also invalidate organization contacts cache
        if org_id is not None:
            cls.invalidate_organization_contacts(org_id)
    
    @classmethod
    def get_organization_contacts(cls, org_id):
        """
        Retrieve all contacts for an organization from cache
        Returns None if not found
        """
        key = cls._get_org_contacts_key(org_id)
        return cache.get(key)
    
    @classmethod
    def set_organization_contacts(cls, org_id, ttl=None, queryset=None):
        """
        Cache all contacts for an organization
        
        Args:
            org_id: Organization ID
            ttl: Time to live in seconds (optional)
            queryset: Optional pre-filtered queryset to use
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_org_contacts_key(org_id)
        
        # Use provided queryset or get all active contacts for organization with related fields
        if queryset is None:
            from .models import Contact  # Import here to avoid circular import
            queryset = Contact.objects.filter(
                organization_id=org_id,
                is_active=True
            ).select_related(
                'organization',
                'created_by',
                'updated_by'
            )
        else:
            # Ensure the queryset has the necessary related fields
            queryset = queryset.select_related(
                'organization',
                'created_by',
                'updated_by'
            )
        
        # Serialize contacts
        from .serializers import ContactSerializer  # Import here to avoid circular import
        serializer = ContactSerializer(queryset, many=True)
        serialized_data = serializer.data
        
        # Ensure we store a list even if it's empty
        if not isinstance(serialized_data, list):
            serialized_data = list(serialized_data)
            
        cache.set(key, serialized_data, timeout=ttl)
        return serialized_data
    
    @classmethod
    def invalidate_organization_contacts(cls, org_id):
        """
        Invalidate the cache for an organization's contacts
        """
        key = cls._get_org_contacts_key(org_id)
        cache.delete(key)
    
    @classmethod
    def bulk_set_contacts(cls, contacts, ttl=None):
        """
        Bulk cache multiple contacts
        
        Args:
            contacts: List of Contact instances
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        # Group contacts by organization
        org_contacts = {}
        for contact in contacts:
            if contact.organization_id not in org_contacts:
                org_contacts[contact.organization_id] = []
            org_contacts[contact.organization_id].append(contact)
            
            # Cache individual contact
            cls.set_contact(contact, ttl=ttl)
        
        # Update organization caches
        for org_id in org_contacts:
            cls.invalidate_organization_contacts(org_id) 