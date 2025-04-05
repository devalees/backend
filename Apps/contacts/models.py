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
        if not skip_validation:
            self.full_clean()
        super().save(*args, **kwargs)
        # Cache the contact after saving
        ContactCache.set_contact(self, include_related=True)

    def hard_delete(self):
        """Hard delete the contact"""
        org_id = self.organization_id
        self.delete(hard_delete=True)
        # Invalidate cache after hard delete
        ContactCache.delete_contact(self.id, org_id)

    def delete(self, *args, **kwargs):
        """Delete the contact"""
        hard_delete = kwargs.pop('hard_delete', False)
        org_id = self.organization_id
        if hard_delete:
            super().delete(*args, **kwargs)
            # Invalidate cache after hard delete
            ContactCache.delete_contact(self.id, org_id)
        else:
            self.is_active = False
            self.save()
            # Update cache with inactive status
            ContactCache.set_contact(self, include_related=True)

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
