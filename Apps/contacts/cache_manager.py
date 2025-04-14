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

class ContactListCache:
    """
    Handles caching operations for ContactList model
    """
    
    LIST_KEY_PREFIX = "list"
    ORG_LISTS_KEY_PREFIX = "org"
    DEFAULT_TTL = getattr(settings, 'CONTACT_CACHE_TTL', 3600)  # 1 hour default
    
    @classmethod
    def _get_list_key(cls, list_id):
        """Generate cache key for a single contact list"""
        return f"{cls.LIST_KEY_PREFIX}:{list_id}"
    
    @classmethod
    def _get_org_lists_key(cls, org_id):
        """Generate cache key for organization lists"""
        return f"{cls.ORG_LISTS_KEY_PREFIX}:{org_id}:lists"
    
    @classmethod
    def get_list(cls, list_id):
        """Retrieve a contact list from cache"""
        key = cls._get_list_key(list_id)
        cached_data = cache.get(key)
        
        if cached_data is None:
            return None
            
        # If the data is already a ContactList instance, return it
        if hasattr(cached_data, '_meta') and cached_data._meta.model_name == 'contactlist':
            return cached_data
            
        # If the data is a dict (serialized), convert it to a model-like object
        if isinstance(cached_data, dict):
            # Create a simple object to hold the serialized data
            from types import SimpleNamespace
            
            # Process any nested serialized data (like contacts)
            if 'contacts' in cached_data and isinstance(cached_data['contacts'], list):
                # Convert contact dictionaries to objects
                contact_objects = []
                for contact_data in cached_data['contacts']:
                    contact_objects.append(SimpleNamespace(**contact_data))
                cached_data['contacts'] = contact_objects
                
            # Convert dict to object with attributes
            return SimpleNamespace(**cached_data)
            
        return None
    
    @classmethod
    def set_list(cls, contact_list, ttl=None, include_related=False):
        """Cache a contact list instance"""
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_list_key(contact_list.id)
        
        # For serialized data with related fields
        if include_related:
            from .serializers import ContactListSerializer
            
            # Use the serializer's context to pass extra data if needed
            context = {'include_only_related_contacts': True}
            serializer = ContactListSerializer(contact_list, context=context)
            cache_data = serializer.data
            
            # Cache the serialized data
            cache.set(key, cache_data, timeout=ttl)
            
            # Also update organization lists cache if org_id exists
            if contact_list.organization_id:
                cls.invalidate_organization_lists(contact_list.organization_id)
                
            # Return the original model instance
            return contact_list
            
        # For non-serialized data, store the model instance directly
        cache.set(key, contact_list, timeout=ttl)
        return contact_list
    
    @classmethod
    def delete_list(cls, list_id, org_id=None, force_delete=False):
        """Delete a contact list from cache"""
        key = cls._get_list_key(list_id)
        
        # Always delete from cache first
        cache.delete(key)
        
        # Always invalidate organization lists if org_id provided
        if org_id:
            cls.invalidate_organization_lists(org_id)
    
    @classmethod
    def get_organization_lists(cls, org_id):
        """
        Retrieve all contact lists for an organization from cache
        Returns None if not found
        """
        key = cls._get_org_lists_key(org_id)
        return cache.get(key)
    
    @classmethod
    def set_organization_lists(cls, org_id, ttl=None, queryset=None):
        """
        Cache all contact lists for an organization
        
        Args:
            org_id: ID of the organization
            ttl: Time to live in seconds (optional)
            queryset: Optional queryset to use instead of fetching from database
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        key = cls._get_org_lists_key(org_id)
        
        # If no queryset provided, fetch from database
        if queryset is None:
            from .models import ContactList
            queryset = ContactList.objects.filter(
                organization_id=org_id,
                is_active=True
            ).select_related('organization').prefetch_related('contacts')
        
        # Convert queryset to list to ensure we can iterate multiple times
        lists = list(queryset)
        
        # Cache individual lists first
        for contact_list in lists:
            cls.set_list(contact_list, ttl=ttl, include_related=True)
        
        # Now cache the organization's list of lists
        cache.set(key, lists, timeout=ttl)
        
        return lists
    
    @classmethod
    def invalidate_organization_lists(cls, org_id):
        """
        Invalidate the cache for all contact lists in an organization
        
        Args:
            org_id: ID of the organization
        """
        key = cls._get_org_lists_key(org_id)
        cache.delete(key)
    
    @classmethod
    def bulk_set_lists(cls, lists, ttl=None):
        """
        Bulk cache multiple contact lists
        
        Args:
            lists: List of ContactList instances
            ttl: Time to live in seconds (optional)
        """
        if ttl is None:
            ttl = cls.DEFAULT_TTL
            
        # Group lists by organization
        org_lists = {}
        for contact_list in lists:
            if not hasattr(contact_list, 'id'):
                continue
                
            org_id = getattr(contact_list, 'organization_id', None)
            if org_id:
                if org_id not in org_lists:
                    org_lists[org_id] = []
                org_lists[org_id].append(contact_list)
            
            # Cache individual list
            cls.set_list(contact_list, ttl=ttl)
        
        # Update organization caches
        for org_id, org_contact_lists in org_lists.items():
            # Cache the organization's lists
            key = cls._get_org_lists_key(org_id)
            cache.set(key, org_contact_lists, timeout=ttl)

class ContactNoteCache:
    """Cache manager for contact notes"""
    
    NOTE_KEY_PREFIX = 'contact_note'
    NOTE_LIST_KEY_PREFIX = 'contact_note_list'
    DEFAULT_TTL = getattr(settings, 'CONTACT_CACHE_TTL', 3600)  # 1 hour default
    
    @classmethod
    def get_note_key(cls, note_id):
        """Get cache key for a note"""
        return f"{cls.NOTE_KEY_PREFIX}:{note_id}"
    
    @classmethod
    def get_note_list_key(cls, contact_id):
        """Get cache key for a contact's note list"""
        return f"{cls.NOTE_LIST_KEY_PREFIX}:{contact_id}"
    
    @classmethod
    def set_note(cls, note, include_related=True):
        """Cache a note and optionally its related data"""
        from django.core.cache import cache
        from rest_framework import serializers
        
        # Get serializer and serialize note
        from .serializers import ContactNoteSerializer
        serializer = ContactNoteSerializer(note)
        note_data = serializer.data
        
        # Cache individual note
        note_key = cls.get_note_key(note.id)
        cache.set(note_key, note_data, timeout=cls.DEFAULT_TTL)
        
        # Update note list cache
        list_key = cls.get_note_list_key(note.contact_id)
        cache.delete(list_key)  # Invalidate list cache
        
        if include_related:
            # Cache related monitoring records
            monitoring_records = note.monitoring_records.all()[:10]  # Cache last 10 records
            from .serializers import ContactNoteMonitoringSerializer
            monitoring_serializer = ContactNoteMonitoringSerializer(monitoring_records, many=True)
            monitoring_data = monitoring_serializer.data
            cache.set(f"{note_key}:monitoring", monitoring_data, timeout=cls.DEFAULT_TTL)
            
            # Cache related notifications
            notifications = note.notifications.all()[:10]  # Cache last 10 notifications
            from .serializers import ContactNoteNotificationSerializer
            notification_serializer = ContactNoteNotificationSerializer(notifications, many=True)
            notification_data = notification_serializer.data
            cache.set(f"{note_key}:notifications", notification_data, timeout=cls.DEFAULT_TTL)
        
        return note_data
    
    @classmethod
    def get_note(cls, note_id):
        """Get a note from cache"""
        from django.core.cache import cache
        from .models import ContactNote
        
        note_key = cls.get_note_key(note_id)
        note_data = cache.get(note_key)
        
        if note_data is None:
            try:
                note = ContactNote.objects.get(id=note_id)
                note_data = cls.set_note(note)
                return note
            except ContactNote.DoesNotExist:
                return None
        
        # Return cached data directly if it's a dict
        if isinstance(note_data, dict):
            return note_data
            
        # Otherwise, convert to ContactNote instance
        return ContactNote(**note_data)
    
    @classmethod
    def get_contact_notes(cls, contact_id, limit=None):
        """Get a contact's notes from cache"""
        from django.core.cache import cache
        from .models import ContactNote
        
        list_key = cls.get_note_list_key(contact_id)
        notes_data = cache.get(list_key)
        
        if notes_data is None:
            # Get notes from database
            notes = ContactNote.objects.filter(
                contact_id=contact_id,
                is_active=True
            ).order_by('-created_at')
            
            if limit:
                notes = notes[:limit]
            
            # Serialize notes
            from .serializers import ContactNoteSerializer
            serializer = ContactNoteSerializer(notes, many=True)
            notes_data = serializer.data
            
            # Cache notes
            cache.set(list_key, notes_data, timeout=cls.DEFAULT_TTL)
            
            # Return database notes
            return notes
        
        # Return notes from cache
        # If it's a list of dicts, return directly
        if isinstance(notes_data, list) and all(isinstance(item, dict) for item in notes_data):
            return [ContactNote(**note_data) for note_data in notes_data]
        
        # Otherwise, return the data as is
        return notes_data
    
    @classmethod
    def delete_note_cache(cls, note_id, contact_id=None):
        """Delete note cache entries"""
        from django.core.cache import cache
        
        # Delete individual note cache
        note_key = cls.get_note_key(note_id)
        cache.delete(note_key)
        cache.delete(f"{note_key}:monitoring")
        cache.delete(f"{note_key}:notifications")
        
        # Delete list cache if contact_id is provided
        if contact_id:
            list_key = cls.get_note_list_key(contact_id)
            cache.delete(list_key)
    
    @classmethod
    def refresh_note_cache(cls, note_id):
        """Refresh a single note in cache"""
        from .models import ContactNote
        
        try:
            note = ContactNote.objects.get(id=note_id, is_active=True)
            cls.set_note(note, include_related=True)
            return True
        except ContactNote.DoesNotExist:
            return False
    
    @classmethod
    def refresh_contact_notes_cache(cls, contact_id):
        """Refresh cache for all notes of a contact"""
        from .models import ContactNote
        
        # Delete existing cache
        list_key = cls.get_note_list_key(contact_id)
        from django.core.cache import cache
        cache.delete(list_key)
        
        # Reload and cache
        notes = ContactNote.objects.filter(
            contact_id=contact_id,
            is_active=True
        ).order_by('-created_at')
        
        # Cache individual notes
        for note in notes:
            cls.set_note(note, include_related=False)
        
        # Cache the list
        from .serializers import ContactNoteSerializer
        serializer = ContactNoteSerializer(notes, many=True)
        notes_data = serializer.data
        
        cache.set(list_key, notes_data, timeout=cls.DEFAULT_TTL)
        return notes_data 