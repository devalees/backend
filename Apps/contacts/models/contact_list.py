from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .base import ContactsBaseModel, Organization
from .contact import Contact
from ..cache_manager import ContactListCache

class ContactList(ContactsBaseModel):
    """ContactList model representing a list of contacts for planning and segmentation"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contact_lists'
    )
    contacts = models.ManyToManyField(
        Contact,
        related_name='lists',
        blank=True
    )
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
        org_id = self.organization_id  # Store org_id before deletion
        
        if hard_delete:
            # Clear cache before hard delete
            ContactListCache.delete_list(self.id, org_id, force_delete=True)
            # Call parent's delete method
            super().delete(*args, **kwargs)
        else:
            # For soft delete, set is_active to False
            self.is_active = False
            self.save()
            # Update cache with inactive state
            ContactListCache.delete_list(self.id, org_id, force_delete=False)

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

@receiver(post_save, sender=ContactList)
def contact_list_post_save(sender, instance, created, **kwargs):
    """Update cache when a contact list is saved"""
    ContactListCache.set_list(instance)
    ContactListCache.invalidate_organization_lists(instance.organization_id)

@receiver(post_delete, sender=ContactList)
def clear_contact_list_cache(sender, instance, **kwargs):
    """Clear cache when a contact list is deleted"""
    ContactListCache.delete_list(instance.id, instance.organization_id, force_delete=True)

class ContactListTemplate(ContactsBaseModel):
    """ContactListTemplate model for defining contact list templates"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contact_list_templates'
    )
    fields = models.JSONField(
        help_text="JSON structure defining the template fields and their properties"
    )
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
