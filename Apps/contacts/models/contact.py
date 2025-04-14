import re
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .base import ContactsBaseModel, User, Organization, Department, Team
from ..cache_manager import ContactCache

class Contact(ContactsBaseModel):
    """Contact model representing a person or organization with task handling capabilities"""
    
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )

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
            
            # Import here to avoid circular import
            from .monitoring import ContactMonitoring
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
        self.delete(hard_delete=True, user=user, request_meta=request_meta)

    def delete(self, *args, **kwargs):
        """Delete the contact"""
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
                from .monitoring import ContactMonitoring
                ContactMonitoring.log_activity(
                    contact=None,  # Don't set contact since it will be deleted
                    user=user,
                    activity_type='delete',
                    description='Hard delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'hard_delete', 'contact_id': self.id},
                    organization=org  # Explicitly set organization
                )
                
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
                from .monitoring import ContactMonitoring
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
