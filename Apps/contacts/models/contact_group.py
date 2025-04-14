from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .base import ContactsBaseModel, Organization
from .contact import Contact

class ContactGroup(ContactsBaseModel):
    """ContactGroup model representing a group of contacts"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
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
        from ..cache_manager import ContactGroupCache
        ContactGroupCache.set_group(self, include_related=True)
        
        # Log the activity
        if hasattr(self, '__class__') and hasattr(self.__class__, 'objects'):
            activity_type = 'create' if is_create else 'update'
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT')
            
            # Import here to avoid circular import
            from .monitoring import ContactGroupMonitoring
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
                from .monitoring import ContactGroupMonitoring
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
            from ..cache_manager import ContactGroupCache
            ContactGroupCache.delete_group(self.id, self.organization_id, force_delete=True)
            
            # Delete all children recursively first
            for child in self.children.all():
                child.delete(hard_delete=True, user=user, request_meta=request_meta)
                
            # Now delete self after children
            super().delete(*args, **kwargs)
        else:
            # Log activity for soft delete
            if user:
                from .monitoring import ContactGroupMonitoring
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
                child.delete(hard_delete=False, user=user, request_meta=request_meta)

    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the contact group"""
        # Log activity before hard delete
        if user and self.organization:
            from .monitoring import ContactGroupMonitoring
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
