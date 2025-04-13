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

    class Meta:
        verbose_name = 'Contact Group'
        verbose_name_plural = 'Contact Groups'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact group"""
        super().save(*args, **kwargs)
        if hasattr(self, '_contacts'):
            self.contacts.set(self._contacts)

    def clean(self):
        """Validate the contact group"""
        super().clean()
        if self.pk and self.contacts.exists():
            # Check if all contacts belong to the same organization
            contacts_orgs = self.contacts.values_list('organization', flat=True).distinct()
            if len(contacts_orgs) > 1 or (len(contacts_orgs) == 1 and contacts_orgs[0] != self.organization.id):
                raise ValidationError("All contacts must belong to the same organization as the group.")

    def delete(self, *args, **kwargs):
        """Delete the contact group"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def hard_delete(self):
        """Hard delete the contact group"""
        self.delete(hard_delete=True)

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
        """Save the template and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            self.full_clean()
        super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the template"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the template"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate template data"""
        # Validate required fields
        if not self.name:
            raise ValidationError({'name': ['Name is required.']})
        if not self.organization:
            raise ValidationError({'organization': ['Organization is required.']})

        # Validate fields structure
        if not isinstance(self.fields, dict):
            raise ValidationError({'fields': ['Fields must be a dictionary.']})

        # Validate each field in the template
        valid_field_types = {'text', 'email', 'phone', 'select', 'number', 'date'}
        for field_name, field_config in self.fields.items():
            if not isinstance(field_config, dict):
                raise ValidationError({
                    'fields': [f'Field {field_name} configuration must be a dictionary.']
                })
            
            # Check required field properties
            if 'type' not in field_config:
                raise ValidationError({
                    'fields': [f'Field {field_name} must have a type.']
                })
            
            if field_config['type'] not in valid_field_types:
                raise ValidationError({
                    'fields': [f'Invalid type for field {field_name}. Must be one of {valid_field_types}']
                })
            
            # Check required property
            if 'required' not in field_config:
                raise ValidationError({
                    'fields': [f'Field {field_name} must specify if it is required.']
                })
            
            if not isinstance(field_config['required'], bool):
                raise ValidationError({
                    'fields': [f'Required property for field {field_name} must be a boolean.']
                })

        # Validate organization constraint
        if self.pk:  # Only check on update
            original = ContactTemplate.objects.get(pk=self.pk)
            if original.organization != self.organization:
                raise ValidationError({
                    'organization': ['Cannot change the organization of a template.']
                })

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
            models.Index(fields=['organization', 'activity_type']),
            models.Index(fields=['user', 'activity_type']),
        ]

    def __str__(self):
        contact_name = self.contact.name if self.contact else "Unknown Contact"
        return f"{self.get_activity_type_display()} - {contact_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @classmethod
    def log_activity(cls, contact=None, user=None, activity_type=None, description=None, 
                    ip_address=None, user_agent=None, metadata=None, organization=None):
        """
        Log an activity record for a contact.
        
        Args:
            contact: The contact this activity is for
            user: The user performing the activity
            activity_type: Type of activity (must be in ACTIVITY_TYPES)
            description: Description of the activity
            ip_address: IP address of the request
            user_agent: User agent of the request
            metadata: Additional metadata about the activity
            organization: The organization this activity is for (if not provided, will be taken from contact)
        """
        if activity_type not in [t[0] for t in cls.ACTIVITY_TYPES]:
            print(f"Warning: Invalid activity type '{activity_type}'")
            return None
            
        # Get organization from contact if available and not explicitly provided
        if not organization and contact:
            organization = getattr(contact, 'organization', None)
            
        if not organization:
            print("Warning: No organization available for monitoring record")
            return None
            
        try:
            # Ensure metadata is a dictionary
            metadata = metadata or {}
            
            # Create monitoring record
            record = cls.objects.create(
                contact=contact,
                user=user,
                activity_type=activity_type,
                description=description,
                organization=organization,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata
            )
            print(f"Created monitoring record: {record.id}, type: {record.activity_type}, desc: {record.description}")
            return record
        except Exception as e:
            print(f"Error creating monitoring record: {str(e)}")
            return None
