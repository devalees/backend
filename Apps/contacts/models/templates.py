from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base import ContactsBaseModel, Organization

class ContactTemplate(ContactsBaseModel):
    """ContactTemplate model for defining contact field templates"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contact_templates'
    )
    fields = models.JSONField(
        help_text="JSON structure defining the template fields and their properties"
    )

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

class ContactGroupTemplate(ContactsBaseModel):
    """ContactGroupTemplate model for defining group templates"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='group_templates'
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
