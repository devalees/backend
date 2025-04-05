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
    def delete_contact(cls, contact_id, org_id):
        """
        Remove a contact from cache
        """
        key = cls._get_contact_key(contact_id)
        cache.delete(key)
        
        # Also invalidate organization contacts cache
        if org_id:
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
    def set_organization_contacts(cls, org_id, ttl=None):
        """
        Cache all contacts for an organization
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_org_contacts_key(org_id)
        
        # Get all contacts for organization with related fields
        from .models import Contact  # Import here to avoid circular import
        contacts = Contact.objects.filter(organization_id=org_id).select_related(
            'organization',
            'created_by',
            'updated_by'
        )
        
        # Serialize contacts
        from .serializers import ContactSerializer  # Import here to avoid circular import
        serializer = ContactSerializer(contacts, many=True)
        cache.set(key, serializer.data, timeout=ttl)
    
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