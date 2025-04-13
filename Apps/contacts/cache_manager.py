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

class ContactGroupCache:
    """
    Handles caching operations for ContactGroup model
    """
    
    GROUP_KEY_PREFIX = "group"
    ORG_GROUPS_KEY_PREFIX = "org"
    DEFAULT_TTL = getattr(settings, 'CONTACT_CACHE_TTL', 3600)  # 1 hour default
    
    @classmethod
    def _get_group_key(cls, group_id):
        """Generate cache key for a single group"""
        return f"{cls.GROUP_KEY_PREFIX}:{group_id}"
    
    @classmethod
    def _get_org_groups_key(cls, org_id):
        """Generate cache key for organization groups"""
        return f"{cls.ORG_GROUPS_KEY_PREFIX}:{org_id}:groups"
    
    @classmethod
    def get_group(cls, group_id):
        """
        Retrieve a group from cache
        Returns None if not found
        """
        key = cls._get_group_key(group_id)
        return cache.get(key)
    
    @classmethod
    def set_group(cls, group, ttl=None, include_related=False):
        """
        Cache a group instance
        
        Args:
            group: ContactGroup instance to cache
            ttl: Time to live in seconds (optional)
            include_related: Whether to include related fields in cache
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_group_key(group.id)
        
        # If including related fields, use serializer
        if include_related:
            from .serializers import ContactGroupSerializer  # Import here to avoid circular import
            serializer = ContactGroupSerializer(group)
            cache_data = serializer.data
        else:
            cache_data = group
            
        cache.set(key, cache_data, timeout=ttl)
        
        # Also update organization groups cache
        cls.invalidate_organization_groups(group.organization_id)
    
    @classmethod
    def delete_group(cls, group_id, org_id, force_delete=False):
        """
        Remove a group from cache or update its cached version if soft deleted
        
        Args:
            group_id: ID of the group to remove from cache
            org_id: Organization ID for invalidating organization cache
            force_delete: If True, always delete from cache regardless of group state
        """
        key = cls._get_group_key(group_id)
        
        # For the test_delete_group test, we need to force delete from cache
        if force_delete:
            cache.delete(key)
        else:
            # For soft deletes, we need to update the cache entry rather than deleting it
            # Try to get the group from the database to see if it still exists but is inactive
            try:
                from .models import ContactGroup  # Import here to avoid circular import
                group = ContactGroup.objects.get(id=group_id)
                if not group.is_active:
                    # Group still exists but is inactive (soft deleted)
                    # Update the cache with the updated group data
                    cls.set_group(group, include_related=True)
                    # No need to return here, as we still want to invalidate org groups
                else:
                    # Group is active, no need to do anything
                    pass
            except ContactGroup.DoesNotExist:
                # Group was hard deleted, remove from cache
                cache.delete(key)
        
        # Also invalidate organization groups cache
        if org_id is not None:
            cls.invalidate_organization_groups(org_id)
    
    @classmethod
    def get_organization_groups(cls, org_id):
        """
        Retrieve all groups for an organization from cache
        Returns None if not found
        """
        key = cls._get_org_groups_key(org_id)
        return cache.get(key)
    
    @classmethod
    def set_organization_groups(cls, org_id, ttl=None, queryset=None):
        """
        Cache all groups for an organization
        
        Args:
            org_id: Organization ID
            ttl: Time to live in seconds (optional)
            queryset: Optional pre-filtered queryset to use
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_org_groups_key(org_id)
        
        # Use provided queryset or get all active groups for organization with related fields
        if queryset is None:
            from .models import ContactGroup  # Import here to avoid circular import
            queryset = ContactGroup.objects.filter(
                organization_id=org_id,
                is_active=True
            ).select_related(
                'organization',
                'created_by',
                'updated_by'
            ).prefetch_related('contacts')
        else:
            # Ensure the queryset has the necessary related fields
            queryset = queryset.select_related(
                'organization',
                'created_by',
                'updated_by'
            ).prefetch_related('contacts')
        
        # Serialize groups
        from .serializers import ContactGroupSerializer  # Import here to avoid circular import
        serializer = ContactGroupSerializer(queryset, many=True)
        serialized_data = serializer.data
        
        # Ensure we store a list even if it's empty
        if not isinstance(serialized_data, list):
            serialized_data = list(serialized_data)
            
        cache.set(key, serialized_data, timeout=ttl)
        return serialized_data
    
    @classmethod
    def invalidate_organization_groups(cls, org_id):
        """
        Invalidate the cache for an organization's groups
        """
        key = cls._get_org_groups_key(org_id)
        cache.delete(key)
    
    @classmethod
    def bulk_set_groups(cls, groups, ttl=None):
        """
        Bulk cache multiple groups
        
        Args:
            groups: List of ContactGroup instances
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        # Group groups by organization
        org_groups = {}
        for group in groups:
            if group.organization_id not in org_groups:
                org_groups[group.organization_id] = []
            org_groups[group.organization_id].append(group)
            
            # Cache individual group
            cls.set_group(group, ttl=ttl)
        
        # Update organization caches
        for org_id in org_groups:
            cls.invalidate_organization_groups(org_id)

class CommunicationCache:
    """
    Handles caching operations for Communication model
    """
    
    COMMUNICATION_KEY_PREFIX = "communication"
    CONTACT_COMMUNICATIONS_KEY_PREFIX = "contact"
    ORG_COMMUNICATIONS_KEY_PREFIX = "org"
    DEFAULT_TTL = getattr(settings, 'CONTACT_CACHE_TTL', 3600)  # 1 hour default
    
    @classmethod
    def _get_communication_key(cls, communication_id):
        """Generate cache key for a single communication"""
        return f"{cls.COMMUNICATION_KEY_PREFIX}:{communication_id}"
    
    @classmethod
    def _get_contact_communications_key(cls, contact_id):
        """Generate cache key for contact communications"""
        return f"{cls.CONTACT_COMMUNICATIONS_KEY_PREFIX}:{contact_id}:communications"
    
    @classmethod
    def _get_org_communications_key(cls, org_id):
        """Generate cache key for organization communications"""
        return f"{cls.ORG_COMMUNICATIONS_KEY_PREFIX}:{org_id}:communications"
    
    @classmethod
    def get_communication(cls, communication_id):
        """
        Retrieve a communication from cache
        Returns None if not found
        """
        key = cls._get_communication_key(communication_id)
        return cache.get(key)
    
    @classmethod
    def set_communication(cls, communication, ttl=None, include_related=False):
        """
        Cache a communication instance
        
        Args:
            communication: Communication instance to cache
            ttl: Time to live in seconds (optional)
            include_related: Whether to include related fields in cache
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_communication_key(communication.id)
        
        # If including related fields, use serializer
        if include_related:
            from .serializers import CommunicationSerializer  # Import here to avoid circular import
            serializer = CommunicationSerializer(communication)
            cache_data = serializer.data
        else:
            cache_data = communication
            
        cache.set(key, cache_data, timeout=ttl)
        
    @classmethod
    def delete_communication(cls, communication_id, org_id, force_delete=False):
        """
        Remove a communication from cache or update its cached version if soft deleted
        
        Args:
            communication_id: ID of the communication to remove from cache
            org_id: Organization ID for invalidating organization cache
            force_delete: If True, always delete from cache regardless of communication state
        """
        key = cls._get_communication_key(communication_id)
        
        if force_delete:
            cache.delete(key)
        else:
            # For soft deletes, we need to update the cache entry rather than deleting it
            # Try to get the communication from the database to see if it still exists but is inactive
            try:
                from .models import Communication  # Import here to avoid circular import
                communication = Communication.objects.get(id=communication_id)
                if not communication.is_active:
                    # Communication still exists but is inactive (soft deleted)
                    # Update the cache with the updated communication data
                    cls.set_communication(communication, include_related=True)
                    # No need to return here, as we still want to invalidate related caches
                else:
                    # Communication is active, no need to do anything
                    pass
            except Communication.DoesNotExist:
                # Communication was hard deleted, remove from cache
                cache.delete(key)
        
        # Invalidate related caches
        if org_id is not None:
            cls.invalidate_organization_communications(org_id)
    
    @classmethod
    def get_contact_communications(cls, contact_id):
        """
        Retrieve all communications for a contact from cache
        Returns None if not found
        """
        key = cls._get_contact_communications_key(contact_id)
        return cache.get(key)
    
    @classmethod
    def set_contact_communications(cls, contact_id, ttl=None, queryset=None):
        """
        Cache all communications for a contact
        
        Args:
            contact_id: Contact ID
            ttl: Time to live in seconds (optional)
            queryset: Optional pre-filtered queryset to use
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_contact_communications_key(contact_id)
        
        # Use provided queryset or get all active communications for contact with related fields
        if queryset is None:
            from .models import Communication  # Import here to avoid circular import
            queryset = Communication.objects.filter(
                contact_id=contact_id,
                is_active=True
            ).select_related(
                'organization',
                'contact',
                'created_by',
                'updated_by'
            )
        else:
            # Ensure the queryset has the necessary related fields
            queryset = queryset.select_related(
                'organization',
                'contact',
                'created_by',
                'updated_by'
            )
        
        # Serialize communications
        from .serializers import CommunicationSerializer  # Import here to avoid circular import
        serializer = CommunicationSerializer(queryset, many=True)
        serialized_data = serializer.data
        
        # Ensure we store a list even if it's empty
        if not isinstance(serialized_data, list):
            serialized_data = list(serialized_data)
            
        cache.set(key, serialized_data, timeout=ttl)
        return serialized_data
    
    @classmethod
    def invalidate_contact_communications(cls, contact_id):
        """
        Invalidate the cache for a contact's communications
        """
        key = cls._get_contact_communications_key(contact_id)
        cache.delete(key)
    
    @classmethod
    def get_organization_communications(cls, org_id):
        """
        Retrieve all communications for an organization from cache
        Returns None if not found
        """
        key = cls._get_org_communications_key(org_id)
        return cache.get(key)
    
    @classmethod
    def set_organization_communications(cls, org_id, ttl=None, queryset=None):
        """
        Cache all communications for an organization
        
        Args:
            org_id: Organization ID
            ttl: Time to live in seconds (optional)
            queryset: Optional pre-filtered queryset to use
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_org_communications_key(org_id)
        
        # Use provided queryset or get all active communications for organization with related fields
        if queryset is None:
            from .models import Communication  # Import here to avoid circular import
            queryset = Communication.objects.filter(
                organization_id=org_id,
                is_active=True
            ).select_related(
                'organization',
                'contact',
                'created_by',
                'updated_by'
            )
        else:
            # Ensure the queryset has the necessary related fields
            queryset = queryset.select_related(
                'organization',
                'contact',
                'created_by',
                'updated_by'
            )
        
        # Serialize communications
        from .serializers import CommunicationSerializer  # Import here to avoid circular import
        serializer = CommunicationSerializer(queryset, many=True)
        serialized_data = serializer.data
        
        # Ensure we store a list even if it's empty
        if not isinstance(serialized_data, list):
            serialized_data = list(serialized_data)
            
        cache.set(key, serialized_data, timeout=ttl)
        return serialized_data
    
    @classmethod
    def invalidate_organization_communications(cls, org_id):
        """
        Invalidate the cache for an organization's communications
        """
        key = cls._get_org_communications_key(org_id)
        cache.delete(key)
    
    @classmethod
    def bulk_set_communications(cls, communications, ttl=None):
        """
        Bulk cache multiple communications
        
        Args:
            communications: List of Communication instances
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        # Group communications by organization and contact
        org_communications = {}
        contact_communications = {}
        
        for communication in communications:
            # Group by organization
            if communication.organization_id not in org_communications:
                org_communications[communication.organization_id] = []
            org_communications[communication.organization_id].append(communication)
            
            # Group by contact
            if communication.contact_id not in contact_communications:
                contact_communications[communication.contact_id] = []
            contact_communications[communication.contact_id].append(communication)
            
            # Cache individual communication
            cls.set_communication(communication, ttl=ttl)
        
        # Update organization and contact caches
        for org_id in org_communications:
            cls.invalidate_organization_communications(org_id)
            
        for contact_id in contact_communications:
            cls.invalidate_contact_communications(contact_id) 