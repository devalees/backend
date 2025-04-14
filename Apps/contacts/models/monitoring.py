from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .base import ContactsBaseModel
from .contact import Contact
from .contact_group import ContactGroup
from .communication import Communication

User = get_user_model()

class ContactMonitoring(ContactsBaseModel):
    """ContactMonitoring model for tracking interactions and activity with contacts"""
    
    ACTIVITY_TYPES = (
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('email', 'Email'),
        ('call', 'Call'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('other', 'Other')
    )
    
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='monitoring_records',
        null=True,  # Allow recording events for deleted contacts
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow system-generated events
        related_name='contact_activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
    )
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Contact Activity Record'
        verbose_name_plural = 'Contact Activity Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact', 'activity_type']),
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['organization', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.contact.name if self.contact else 'Deleted Contact'} - {self.created_at}"

    @classmethod
    def log_activity(cls, contact=None, user=None, activity_type=None, description=None, 
                    ip_address=None, user_agent=None, metadata=None, organization=None):
        """Log an activity for a contact"""
        if contact and not organization:
            organization = contact.organization
            
        if not organization and contact:
            organization = contact.organization
            
        record = cls.objects.create(
            contact=contact,
            user=user,
            activity_type=activity_type,
            description=description,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        return record

class ContactGroupMonitoring(ContactsBaseModel):
    """ContactGroupMonitoring model for tracking interactions and activity with contact groups"""
    
    ACTIVITY_TYPES = (
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('add_contact', 'Add Contact'),
        ('remove_contact', 'Remove Contact'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('other', 'Other')
    )
    
    group = models.ForeignKey(
        ContactGroup,
        on_delete=models.CASCADE,
        related_name='monitoring_records',
        null=True,  # Allow recording events for deleted groups
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow system-generated events
        related_name='group_activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
    )
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Contact Group Activity Record'
        verbose_name_plural = 'Contact Group Activity Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'activity_type']),
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['organization', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.group.name if self.group else 'Deleted Group'} - {self.created_at}"

    @classmethod
    def log_activity(cls, group=None, user=None, activity_type=None, description=None, 
                    ip_address=None, user_agent=None, metadata=None, organization=None):
        """Log an activity for a contact group"""
        if group and not organization:
            organization = group.organization
            
        if not organization and group:
            organization = group.organization
            
        record = cls.objects.create(
            group=group,
            user=user,
            activity_type=activity_type,
            description=description,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        return record

class CommunicationMonitoring(ContactsBaseModel):
    """CommunicationMonitoring model for tracking interactions with communications"""
    
    ACTIVITY_TYPES = (
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('send', 'Send'),
        ('schedule', 'Schedule'),
        ('cancel', 'Cancel'),
        ('open', 'Open'),
        ('click', 'Click'),
        ('other', 'Other')
    )
    
    communication = models.ForeignKey(
        Communication,
        on_delete=models.CASCADE,
        related_name='monitoring_records',
        null=True,  # Allow recording events for deleted communications
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow system-generated events
        related_name='communication_activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
    )
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Communication Activity Record'
        verbose_name_plural = 'Communication Activity Records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['communication']),
            models.Index(fields=['user']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['organization']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        if self.communication:
            return f"{self.activity_type} - {self.communication.subject}"
        return f"{self.activity_type} - {self.description}"
    
    @classmethod
    def log_activity(cls, communication=None, user=None, activity_type=None, description=None, 
                    ip_address=None, user_agent=None, metadata=None, organization=None):
        """Create an activity record for a communication"""
        if metadata is None:
            metadata = {}
            
        # Get organization from communication if not provided
        if organization is None and communication is not None:
            organization = communication.organization
            
        if organization is None:
            raise ValueError("Organization must be provided if communication is None")
            
        activity = cls.objects.create(
            communication=communication,
            user=user,
            activity_type=activity_type,
            description=description,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        
        return activity
