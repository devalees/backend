from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from Apps.core.models import TaskAwareModel
from Apps.entity.models import Organization, Department, Team
from .cache_manager import ContactCache
import re
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

User = get_user_model()

class Contact(TaskAwareModel):
    """Contact model representing a person or organization with task handling capabilities"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_updated'
    )
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'entity.Department',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    team = models.ForeignKey(
        'entity.Team',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        # Determine if this is a create or update
        is_create = self._state.adding
        
        if not skip_validation:
            self.full_clean()
            
        super().save(*args, **kwargs)
        
        # Cache the contact after saving
        ContactCache.set_contact(self, include_related=True)
        
        # Log the activity
        if hasattr(self, '__class__') and hasattr(self.__class__, 'objects'):
            activity_type = 'create' if is_create else 'update'
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT')
            
            # Import here to avoid circular import, and only if needed
            from Apps.contacts.models import ContactMonitoring
            ContactMonitoring.log_activity(
                contact=self,
                user=user,
                activity_type=activity_type,
                description=f"{'Created' if is_create else 'Updated'} via model save",
                ip_address=ip_address,
                user_agent=user_agent
            )

    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the contact"""
        # Call delete with hard_delete=True
        self.delete(hard_delete=True, user=user, request_meta=request_meta)

    def delete(self, *args, **kwargs):
        """Delete the contact"""
        hard_delete = kwargs.pop('hard_delete', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        org_id = self.organization_id
        org = self.organization
        
        print("\nDebug delete method:")
        print(f"hard_delete: {hard_delete}")
        print(f"user: {user}")
        print(f"request_meta: {request_meta}")
        print(f"org_id: {org_id}")
        print(f"organization: {org}")
        
        if hard_delete:
            # Log before deleting
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                from Apps.contacts.models import ContactMonitoring
                print("\nCreating hard delete monitoring record...")
                record = ContactMonitoring.log_activity(
                    contact=None,  # Don't set contact since it will be deleted
                    user=user,
                    activity_type='delete',
                    description='Hard delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'hard_delete', 'contact_id': self.id},
                    organization=org  # Explicitly set organization
                )
                print(f"Created record: {record.id}, {record.description}")
                
            # Call the parent class's delete method
            super().delete(*args, **kwargs)
        else:
            # Soft delete - set is_active to False
            self.is_active = False
            self.save(skip_validation=True)
            
            # Log the soft delete activity
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                from Apps.contacts.models import ContactMonitoring
                ContactMonitoring.log_activity(
                    contact=self,
                    user=user,
                    activity_type='delete',
                    description='Soft delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'soft_delete', 'contact_id': self.id},
                    organization=org
                )

    def clean(self):
        """Validate contact data"""
        # Validate email format
        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError({'email': ['Enter a valid email address.']})

        # Validate phone format (simple validation for demonstration)
        phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        if not phone_pattern.match(self.phone):
            raise ValidationError({'phone': ['Enter a valid phone number (9-15 digits, optionally starting with + and country code).']})

        # Validate department belongs to organization
        if self.department and self.department.organization != self.organization:
            raise ValidationError({'department': ['Department must belong to the contact\'s organization.']})

        # Validate team belongs to department
        if self.team:
            if not self.department:
                raise ValidationError({'team': ['Cannot assign team without department.']})
            if self.team.department != self.department:
                raise ValidationError({'team': ['Team must belong to the contact\'s department.']})

@receiver(post_save, sender=Contact)
def contact_post_save(sender, instance, created, **kwargs):
    """Update cache when contact is saved"""
    ContactCache.set_contact(instance, include_related=True)
    ContactCache.invalidate_organization_contacts(instance.organization_id)

@receiver(post_delete, sender=Contact)
def contact_post_delete(sender, instance, **kwargs):
    """Update cache when contact is deleted"""
    ContactCache.delete_contact(instance.id, instance.organization_id)

class ContactGroup(models.Model):
    """ContactGroup model representing a group of contacts"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_groups_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_groups_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_groups',
        null=True,
        blank=True
    )
    contacts = models.ManyToManyField(
        Contact,
        related_name='groups',
        blank=True
    )
    is_active = models.BooleanField(default=True)
    # Add parent field for hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name = 'Contact Group'
        verbose_name_plural = 'Contact Groups'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact group"""
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        # Determine if this is a create or update
        is_create = self._state.adding
        
        # Validate before saving
        self.full_clean()
        
        super().save(*args, **kwargs)
        
        if hasattr(self, '_contacts'):
            self.contacts.set(self._contacts)
            
        # Cache the group after saving
        from .cache_manager import ContactGroupCache
        ContactGroupCache.set_group(self, include_related=True)
        
        # Log the activity
        if hasattr(self, '__class__') and hasattr(self.__class__, 'objects'):
            activity_type = 'create' if is_create else 'update'
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT')
            
            # Import here to avoid circular import
            from Apps.contacts.models import ContactGroupMonitoring
            ContactGroupMonitoring.log_activity(
                group=self,
                user=user,
                activity_type=activity_type,
                description=f"{'Created' if is_create else 'Updated'} via model save",
                ip_address=ip_address,
                user_agent=user_agent
            )

    def clean(self):
        """Validate the contact group"""
        super().clean()
        
        # Check for circular references
        if self.parent:
            if self.parent == self:
                raise ValidationError("A group cannot be its own parent.")
            
            # Check for circular references in the hierarchy
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Circular reference detected in group hierarchy.")
                current = current.parent
        
        if self.pk and self.contacts.exists():
            # Check if all contacts belong to the same organization
            contacts_orgs = self.contacts.values_list('organization', flat=True).distinct()
            if len(contacts_orgs) > 1 or (len(contacts_orgs) == 1 and contacts_orgs[0] != self.organization.id):
                raise ValidationError("All contacts must belong to the same organization as the group.")

    def delete(self, *args, **kwargs):
        """Delete the contact group"""
        hard_delete = kwargs.pop('hard_delete', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        if hard_delete:
            # Log activity before hard delete
            if user:
                from Apps.contacts.models import ContactGroupMonitoring
                ContactGroupMonitoring.log_activity(
                    group=None,  # Set to None since the group will be deleted
                    user=user,
                    activity_type='delete',
                    description='Hard delete',
                    ip_address=request_meta.get('REMOTE_ADDR'),
                    user_agent=request_meta.get('HTTP_USER_AGENT'),
                    metadata={'method': 'hard_delete', 'group_id': self.id},
                    organization=self.organization
                )
            
            # Delete from cache
            from .cache_manager import ContactGroupCache
            ContactGroupCache.delete_group(self.id, self.organization_id, force_delete=True)
            
            # Delete all children recursively first
            for child in self.children.all():
                child.delete(hard_delete=True, user=user, request_meta=request_meta)
                
            # Now delete self after children
            super().delete(*args, **kwargs)
        else:
            # Log activity for soft delete
            if user:
                from Apps.contacts.models import ContactGroupMonitoring
                ContactGroupMonitoring.log_activity(
                    group=self,
                    user=user,
                    activity_type='delete',
                    description='Soft delete',
                    ip_address=request_meta.get('REMOTE_ADDR'),
                    user_agent=request_meta.get('HTTP_USER_AGENT'),
                    metadata={'method': 'soft_delete'}
                )
            
            self.is_active = False
            self.save()
            
            # Soft delete all children recursively
            for child in self.children.all():
                # Use hard_delete=False explicitly to ensure we're doing soft delete
                child.delete(hard_delete=False, user=user, request_meta=request_meta)

    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the contact group"""
        # Log activity before hard delete
        if user and self.organization:
            from Apps.contacts.models import ContactGroupMonitoring
            ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
            user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
            
            # Create monitoring record with explicit organization
            ContactGroupMonitoring.log_activity(
                group=None,  # Group will be deleted, so don't reference it directly
                user=user,
                activity_type='delete',
                description='Hard delete',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'method': 'hard_delete', 'group_id': self.id},
                organization=self.organization
            )
            
        # Call delete with hard_delete=True
        self.delete(hard_delete=True, user=user, request_meta=request_meta)
        
    def get_ancestors(self):
        """Get all ancestors of this group"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
        
    def get_descendants(self):
        """Get all descendants of this group"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
        
    @classmethod
    def create_from_template(cls, template, **kwargs):
        """Create a new group from a template"""
        group = cls(
            name=template.name,
            description=template.description,
            organization=template.organization,
            **kwargs
        )
        group.save()
        return group
        
    def apply_template(self, template):
        """Apply a template to this group"""
        self.name = template.name
        self.description = template.description
        self.save()

class ContactTemplate(models.Model):
    """ContactTemplate model for defining contact field templates"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_templates_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_templates_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_templates'
    )
    fields = models.JSONField(
        help_text="JSON structure defining the template fields and their properties"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Contact Template'
        verbose_name_plural = 'Contact Templates'
        ordering = ['name']
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact template"""
        super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the contact template"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the contact template"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate the contact template"""
        super().clean()
        
        # Validate fields structure
        if not isinstance(self.fields, dict):
            raise ValidationError("Fields must be a dictionary.")
            
        # Define allowed field types
        allowed_types = ['text', 'number', 'email', 'phone', 'date', 'boolean', 'select']
            
        for field_name, field_props in self.fields.items():
            if not isinstance(field_props, dict):
                raise ValidationError(f"Field properties for {field_name} must be a dictionary.")
                
            # Check required properties
            if 'type' not in field_props:
                raise ValidationError(f"Field {field_name} must have a type.")
                
            # Check if type is valid
            if field_props['type'] not in allowed_types:
                raise ValidationError(f"Field {field_name} has invalid type '{field_props['type']}'. Allowed types: {', '.join(allowed_types)}")
                
            if 'required' not in field_props:
                raise ValidationError(f"Field {field_name} must specify if it's required.")
                
            if not isinstance(field_props['required'], bool):
                raise ValidationError(f"Field {field_name} 'required' property must be a boolean.")

class ContactGroupTemplate(models.Model):
    """ContactGroupTemplate model for defining group templates"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_templates_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='group_templates_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='group_templates'
    )
    fields = models.JSONField(
        help_text="JSON structure defining the template fields and their properties"
    )
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name = 'Contact Group Template'
        verbose_name_plural = 'Contact Group Templates'
        ordering = ['name']
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the group template"""
        # Increment version on update
        if self.pk:
            self.version += 1
            
        super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the group template"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the group template"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate the group template"""
        super().clean()
        
        # Validate fields structure
        if not isinstance(self.fields, dict):
            raise ValidationError("Fields must be a dictionary.")
            
        for field_name, field_props in self.fields.items():
            if not isinstance(field_props, dict):
                raise ValidationError(f"Field properties for {field_name} must be a dictionary.")
                
            # Check required properties
            if 'type' not in field_props:
                raise ValidationError(f"Field {field_name} must have a type.")
                
            if 'required' not in field_props:
                raise ValidationError(f"Field {field_name} must specify if it's required.")
                
            if not isinstance(field_props['required'], bool):
                raise ValidationError(f"Field {field_name} 'required' property must be a boolean.")
                
        # Check for circular references
        if self.parent:
            if self.parent == self:
                raise ValidationError("A template cannot be its own parent.")
            
            # Check for circular references in the hierarchy
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Circular reference detected in template hierarchy.")
                current = current.parent

class ContactMonitoring(models.Model):
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
    
    created_at = models.DateTimeField(auto_now_add=True)
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
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_monitoring_records'
    )
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
        """
        Log an activity for a contact
        
        Args:
            contact: Contact instance or None
            user: User instance or None
            activity_type: Type of activity
            description: Description of the activity
            ip_address: IP address of the request
            user_agent: User agent of the request
            metadata: Additional metadata
            organization: Organization instance or None
            
        Returns:
            Created monitoring record
        """
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

class ContactGroupMonitoring(models.Model):
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
    
    created_at = models.DateTimeField(auto_now_add=True)
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
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='group_monitoring_records'
    )
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
        """
        Log an activity for a contact group
        
        Args:
            group: ContactGroup instance or None
            user: User instance or None
            activity_type: Type of activity
            description: Description of the activity
            ip_address: IP address of the request
            user_agent: User agent of the request
            metadata: Additional metadata
            organization: Organization instance or None
            
        Returns:
            Created monitoring record
        """
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

class Communication(models.Model):
    """Communication model for tracking messages sent to contacts"""
    
    COMMUNICATION_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('call', 'Call'),
        ('letter', 'Letter'),
        ('meeting', 'Meeting'),
        ('other', 'Other')
    )
    
    STATUS_TYPES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communications_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communications_updated'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='communications'
    )
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='communications'
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    communication_type = models.CharField(
        max_length=20,
        choices=COMMUNICATION_TYPES,
        default='email'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_TYPES,
        default='draft'
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Communication'
        verbose_name_plural = 'Communications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact']),
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
            models.Index(fields=['communication_type']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return self.subject
    
    @property
    def is_sent(self):
        """Return True if the communication has been sent"""
        return self.status == 'sent'
    
    @property
    def is_failed(self):
        """Return True if the communication has failed"""
        return self.status == 'failed'
    
    def save(self, *args, **kwargs):
        """Save the communication and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        # Determine if this is a create or update
        is_create = self._state.adding
        
        if not skip_validation:
            self.full_clean()
            
        # If status is transitioning to 'sent', update sent_at
        if self.status == 'sent' and (is_create or not Communication.objects.get(pk=self.pk).is_sent):
            self.sent_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Cache the communication
        from .cache_manager import CommunicationCache
        CommunicationCache.set_communication(self, include_related=True)
        
        # Log the activity
        if hasattr(self, '__class__') and hasattr(self.__class__, 'objects'):
            activity_type = 'create' if is_create else 'update'
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT')
            
            CommunicationMonitoring.log_activity(
                communication=self,
                user=user,
                activity_type=activity_type,
                description=f"{'Created' if is_create else 'Updated'} via model save",
                ip_address=ip_address,
                user_agent=user_agent
            )
    
    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the communication"""
        self.delete(hard_delete=True, user=user, request_meta=request_meta)
    
    def delete(self, *args, **kwargs):
        """Delete the communication"""
        hard_delete = kwargs.pop('hard_delete', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        org_id = self.organization_id
        org = self.organization
        
        if hard_delete:
            # Log before deleting
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                
                CommunicationMonitoring.log_activity(
                    communication=None,  # Don't set communication since it will be deleted
                    user=user,
                    activity_type='delete',
                    description='Hard delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'hard_delete', 'communication_id': self.id},
                    organization=org  # Explicitly set organization
                )
                
            # Call the parent class's delete method
            super().delete(*args, **kwargs)
            
            # Clear cache
            from .cache_manager import CommunicationCache
            CommunicationCache.delete_communication(self.id, org_id, force_delete=True)
        else:
            # Soft delete - set is_active to False
            self.is_active = False
            self.save(skip_validation=True)
            
            # Log the soft delete activity
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                
                CommunicationMonitoring.log_activity(
                    communication=self,
                    user=user,
                    activity_type='delete',
                    description='Soft delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'soft_delete', 'communication_id': self.id},
                    organization=org
                )
    
    def clean(self):
        """Validate communication data"""
        # Validate communication type
        valid_types = dict(self.COMMUNICATION_TYPES).keys()
        if self.communication_type not in valid_types:
            raise ValidationError({'communication_type': [f'Invalid communication type. Must be one of {valid_types}']})
        
        # Validate status
        valid_statuses = dict(self.STATUS_TYPES).keys()
        if self.status not in valid_statuses:
            raise ValidationError({'status': [f'Invalid status. Must be one of {valid_statuses}']})
        
        # Validate scheduled communication
        if self.status == 'scheduled' and not self.scheduled_at:
            raise ValidationError({'scheduled_at': ['Scheduled communications must have a scheduled date and time.']})
        
        # Check if contact belongs to the organization
        if self.contact and self.contact.organization != self.organization:
            raise ValidationError({'contact': ['Contact must belong to the communication\'s organization.']})


@receiver(post_save, sender=Communication)
def communication_post_save(sender, instance, created, **kwargs):
    """Update cache when communication is saved"""
    from .cache_manager import CommunicationCache
    CommunicationCache.set_communication(instance, include_related=True)
    CommunicationCache.invalidate_contact_communications(instance.contact_id)
    CommunicationCache.invalidate_organization_communications(instance.organization_id)

@receiver(post_delete, sender=Communication)
def communication_post_delete(sender, instance, **kwargs):
    """Update cache when communication is deleted"""
    from .cache_manager import CommunicationCache
    CommunicationCache.delete_communication(instance.id, instance.organization_id)


class CommunicationTemplate(models.Model):
    """CommunicationTemplate model for defining message templates"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communication_templates_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communication_templates_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='communication_templates'
    )
    subject_template = models.CharField(max_length=255)
    message_template = models.TextField()
    communication_type = models.CharField(
        max_length=20,
        choices=Communication.COMMUNICATION_TYPES,
        default='email'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Communication Template'
        verbose_name_plural = 'Communication Templates'
        ordering = ['name']
        unique_together = ['name', 'organization']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Save the template"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def hard_delete(self):
        """Hard delete the template"""
        super().delete()
        
    def delete(self, *args, **kwargs):
        """Soft delete the template"""
        self.is_active = False
        self.save()
        
    def clean(self):
        """Validate template"""
        # Validate communication type
        valid_types = dict(Communication.COMMUNICATION_TYPES).keys()
        if self.communication_type not in valid_types:
            raise ValidationError({'communication_type': [f'Invalid communication type. Must be one of {valid_types}']})
    
    def create_communication(self, contact, user=None):
        """
        Create a communication based on this template
        
        Args:
            contact: Contact to create communication for
            user: User creating the communication
        
        Returns:
            New Communication instance
        """
        # Validate contact belongs to same organization
        if contact.organization != self.organization:
            raise ValidationError('Contact must belong to the same organization as the template')
        
        # Simple template rendering using string replacement
        # In a real app, you might use a more robust template engine
        context = {'contact': contact}
        
        # Render subject and message
        subject = self._render_template(self.subject_template, context)
        message = self._render_template(self.message_template, context)
        
        # Create communication
        communication = Communication.objects.create(
            contact=contact,
            organization=self.organization,
            subject=subject,
            message=message,
            communication_type=self.communication_type,
            status='draft',
            created_by=user,
            updated_by=user
        )
        
        return communication
    
    def _render_template(self, template_string, context):
        """
        Render template with context data
        
        Args:
            template_string: Template string with placeholders
            context: Dict with objects to use for rendering
        
        Returns:
            Rendered string
        """
        # Replace {{var}} placeholders
        # This is a simple implementation - a real app would use a proper template engine
        result = template_string
        
        # Handle {{contact.attribute}} replacements
        if 'contact' in context:
            contact = context['contact']
            for field in ['name', 'email', 'phone']:
                placeholder = f'{{{{contact.{field}}}}}'
                value = getattr(contact, field, '')
                result = result.replace(placeholder, str(value))
        
        return result


class CommunicationMonitoring(models.Model):
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
    
    created_at = models.DateTimeField(auto_now_add=True)
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
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='communication_monitoring_records'
    )
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
        """
        Create an activity record for a communication
        
        Args:
            communication: Communication object (optional, for deleted communications)
            user: User who performed the activity
            activity_type: Type of activity (view, create, etc.)
            description: Description of activity
            ip_address: IP address of user (for web activities)
            user_agent: User agent string (for web activities)
            metadata: Additional JSON data
            organization: Organization (required if communication is None)
            
        Returns:
            New CommunicationMonitoring instance
        """
        if metadata is None:
            metadata = {}
            
        # Get organization from communication if not provided
        if organization is None and communication is not None:
            organization = communication.organization
            
        if organization is None:
            raise ValueError("Organization must be provided if communication is None")
            
        activity = cls(
            communication=communication,
            user=user,
            activity_type=activity_type,
            description=description,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        activity.save()
        
        return activity

class ContactList(models.Model):
    """ContactList model representing a list of contacts for planning and segmentation"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_lists_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_lists_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_lists'
    )
    contacts = models.ManyToManyField(
        Contact,
        related_name='lists',
        blank=True
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Contact List'
        verbose_name_plural = 'Contact Lists'
        ordering = ['name']
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the contact list"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the contact list"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate the contact list."""
        super().clean()
        
        if not self.name:
            raise ValidationError({'name': _('Name is required')})
        
        if not self.organization_id:
            raise ValidationError({'organization': _('Organization is required')})

        # Check name uniqueness within organization
        if ContactList.objects.filter(
            organization=self.organization,
            name=self.name
        ).exclude(pk=self.pk).exists():
            raise ValidationError({
                'name': _('A contact list with this name already exists in this organization')
            })
        
        # Validate metadata format
        if self.metadata and not isinstance(self.metadata, dict):
            raise ValidationError({'metadata': _('Metadata must be a valid JSON object')})

        # Only check contacts if the instance has been saved
        if self.pk and self.contacts.exists():
            # Check that all contacts belong to the same organization
            invalid_contacts = self.contacts.exclude(organization=self.organization)
            if invalid_contacts.exists():
                raise ValidationError({
                    'contacts': _('All contacts must belong to the same organization as the contact list')
                })

class ContactListTemplate(models.Model):
    """ContactListTemplate model for defining contact list templates"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_list_templates_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_list_templates_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_list_templates'
    )
    fields = models.JSONField(
        help_text="JSON structure defining the template fields and their properties"
    )
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    class Meta:
        verbose_name = 'Contact List Template'
        verbose_name_plural = 'Contact List Templates'
        ordering = ['name']
        unique_together = ['name', 'organization']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the template"""
        super().delete()

    def delete(self, *args, **kwargs):
        """Soft delete the template"""
        self.is_active = False
        self.save()

    def clean(self):
        """Validate the template."""
        super().clean()
        
        if not self.name:
            raise ValidationError({'name': _('Name is required')})
        
        if not self.organization_id:
            raise ValidationError({'organization': _('Organization is required')})

        # Check name uniqueness within organization
        if ContactListTemplate.objects.filter(
            organization=self.organization,
            name=self.name
        ).exclude(pk=self.pk).exists():
            raise ValidationError({
                'name': _('A template with this name already exists in this organization')
            })
        
        # Validate fields format
        if not isinstance(self.fields, dict):
            raise ValidationError({'fields': _('Fields must be a valid JSON object')})
        
        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in self.fields:
                raise ValidationError({
                    'fields': _(f'Fields must contain a {field} field')
                })
        
        # Validate field properties
        for field_name, field_props in self.fields.items():
            if not isinstance(field_props, dict):
                raise ValidationError({
                    'fields': _(f'Field {field_name} must be a valid JSON object')
                })
            
            if 'type' not in field_props:
                raise ValidationError({
                    'fields': _(f'Field {field_name} must have a type property')
                })
            
            if 'required' not in field_props:
                raise ValidationError({
                    'fields': _(f'Field {field_name} must have a required property')
                })

    def create_contact_list(self, user=None):
        """Create a new contact list from this template"""
        contact_list = ContactList(
            name=self.name,
            description=self.description,
            organization=self.organization,
            created_by=user or self.created_by,
            updated_by=user or self.updated_by
        )
        contact_list.save()
        return contact_list

    def apply_template(self, contact_list):
        """Apply this template to an existing contact list"""
        contact_list.name = self.name
        contact_list.description = self.description
        contact_list.save()

    def get_ancestors(self):
        """Get all ancestors of this template"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendants of this template"""
        descendants = []
        children = ContactListTemplate.objects.filter(parent=self)
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

class ContactSegment(models.Model):
    """ContactSegment model for defining segments within a contact list based on filter criteria"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_segments_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_segments_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    contact_list = models.ForeignKey(
        ContactList,
        on_delete=models.CASCADE,
        related_name='segments'
    )
    filter_criteria = models.JSONField(
        help_text="JSON structure defining the filter criteria for the segment"
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Contact Segment'
        verbose_name_plural = 'Contact Segments'
        ordering = ['name']
        unique_together = ['name', 'contact_list']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def hard_delete(self, user=None, request_meta=None):
        """Permanently delete the contact segment"""
        super().delete()
    
    def delete(self, *args, **kwargs):
        """Soft delete the contact segment"""
        self.is_active = False
        self.save()
    
    def clean(self):
        """Validate the contact segment"""
        if not self.name:
            raise ValidationError({'name': _('Name is required')})
        
        if self.contact_list is None:
            raise ValidationError({'contact_list': _('Contact list is required')})
        
        # Validate filter criteria
        if not isinstance(self.filter_criteria, dict):
            raise ValidationError({'filter_criteria': _('Filter criteria must be a dictionary')})
        
        # Validate filter criteria structure
        self._validate_filter_criteria(self.filter_criteria)
        
        # Validate metadata is a dictionary
        if not isinstance(self.metadata, dict):
            raise ValidationError({'metadata': _('Metadata must be a dictionary')})
    
    def _validate_filter_criteria(self, criteria):
        """Validate the structure of filter criteria"""
        # Check for simple criteria
        if 'field' in criteria and 'operator' in criteria and 'value' in criteria:
            return
        
        # Check for complex criteria with AND/OR operators
        if 'operator' in criteria and criteria['operator'] in ['and', 'or']:
            if 'criteria' not in criteria or not isinstance(criteria['criteria'], list):
                raise ValidationError({
                    'filter_criteria': _('Complex criteria must have a list of sub-criteria')
                })
            
            # Validate each sub-criteria
            for sub_criteria in criteria['criteria']:
                self._validate_filter_criteria(sub_criteria)
        else:
            raise ValidationError({
                'filter_criteria': _('Invalid filter criteria structure')
            })
    
    def get_matching_contacts(self):
        """Get contacts that match the filter criteria"""
        contacts = self.contact_list.contacts.all()
        return self._apply_filter_criteria(contacts, self.filter_criteria)
    
    def _apply_filter_criteria(self, contacts, criteria):
        """Apply filter criteria to a queryset of contacts"""
        # Handle simple criteria
        if 'field' in criteria and 'operator' in criteria and 'value' in criteria:
            field = criteria['field']
            operator = criteria['operator']
            value = criteria['value']
            
            if operator == 'equals':
                return contacts.filter(**{field: value})
            elif operator == 'contains':
                # Use icontains for case-insensitive contains
                return contacts.filter(**{f"{field}__icontains": value})
            elif operator == 'startswith':
                return contacts.filter(**{f"{field}__istartswith": value})
            elif operator == 'endswith':
                return contacts.filter(**{f"{field}__iendswith": value})
            elif operator == 'gt':
                return contacts.filter(**{f"{field}__gt": value})
            elif operator == 'gte':
                return contacts.filter(**{f"{field}__gte": value})
            elif operator == 'lt':
                return contacts.filter(**{f"{field}__lt": value})
            elif operator == 'lte':
                return contacts.filter(**{f"{field}__lte": value})
            elif operator == 'in':
                return contacts.filter(**{f"{field}__in": value})
            else:
                return contacts.none()
        
        # Handle complex criteria with AND/OR operators
        if 'operator' in criteria and criteria['operator'] in ['and', 'or']:
            sub_criteria = criteria['criteria']
            
            if not sub_criteria:
                return contacts
            
            # Start with the first sub-criteria
            result = self._apply_filter_criteria(contacts, sub_criteria[0])
            
            # Apply the rest of the sub-criteria
            for sub_criteria_item in sub_criteria[1:]:
                sub_result = self._apply_filter_criteria(contacts, sub_criteria_item)
                
                if criteria['operator'] == 'and':
                    # Use filter() instead of intersection() to avoid subquery issues
                    result = result.filter(id__in=sub_result.values_list('id', flat=True))
                else:  # 'or'
                    # Use union() with distinct() to avoid duplicates
                    result = result.union(sub_result).distinct()
            
            return result
        
        return contacts.none()
