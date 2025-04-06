from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from Apps.entity.models import Organization
import re

class RBACBaseModel(models.Model):
    """
    Abstract base model for RBAC implementation with organization isolation support.
    Provides common fields and methods for all RBAC-related models.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='%(class)s_related'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        app_label = 'rbac'
        abstract = True

    def get_permission_cache_key(self, user, permission):
        """Generate cache key for permission checks"""
        return f"rbac_permission_{self.__class__.__name__}_{self.id}_{user.id}_{permission}"

    def has_permission(self, user, permission):
        """
        Check if user has specific permission on this object
        Uses caching to improve performance
        """
        cache_key = self.get_permission_cache_key(user, permission)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result

        # Implement permission check logic here
        # This is a placeholder - actual implementation will be added in subsequent steps
        result = False
        
        # Cache the result
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
        return result

    def get_field_permission(self, user, field_name):
        """
        Check if user has permission to access specific field
        """
        # Implement field-level permission check logic here
        # This is a placeholder - actual implementation will be added in subsequent steps
        return True

    def invalidate_permission_cache(self, user=None):
        """
        Invalidate permission cache for this object
        """
        if user:
            # Invalidate specific user's permissions
            cache.delete_pattern(f"rbac_permission_{self.__class__.__name__}_{self.id}_{user.id}_*")
        else:
            # Invalidate all users' permissions
            cache.delete_pattern(f"rbac_permission_{self.__class__.__name__}_{self.id}_*_*")

class Role(RBACBaseModel):
    """
    Role model for implementing role-based access control.
    Supports role hierarchy and permission inheritance.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'rbac'
        unique_together = ('name', 'organization')
        ordering = ['name']

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError({'name': 'Role name cannot be empty'})
        
        if not re.match(r'^[a-zA-Z0-9_\s-]+$', self.name):
            raise ValidationError({'name': 'Role name can only contain letters, numbers, spaces, underscores, and hyphens'})
        
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError({'parent': 'Parent role must belong to the same organization'})
        
        # Check for circular references
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError({'parent': 'Circular reference detected in role hierarchy'})
                current = current.parent

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_permission_cache_key(self, permission):
        """Generate cache key for permission checks"""
        return f"role_permission_{self.id}_{permission}"

    def add_permission(self, permission):
        """Add a permission to the role"""
        if not self.permissions:
            self.permissions = {}
        if permission not in self.permissions:
            self.permissions[permission] = True
            self.save()
            cache.delete(self.get_permission_cache_key(permission))

    def remove_permission(self, permission):
        """Remove a permission from the role"""
        if self.permissions and permission in self.permissions:
            del self.permissions[permission]
            self.save()
            cache.delete(self.get_permission_cache_key(permission))

    def has_permission(self, permission):
        """Check if the role has a specific permission"""
        cache_key = self.get_permission_cache_key(permission)
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        has_perm = permission in self.get_all_permissions()
        cache.set(cache_key, has_perm, timeout=3600)
        return has_perm

    def get_all_permissions(self):
        """Get all permissions including inherited ones"""
        permissions = set(self.permissions.keys() if self.permissions else set())
        if self.parent:
            permissions.update(self.parent.get_all_permissions())
        return permissions

    def deactivate(self):
        """Deactivate the role"""
        self.is_active = False
        self.save()

    def activate(self):
        """Activate the role"""
        self.is_active = True
        self.save()

    def __str__(self):
        return self.name

class Permission(RBACBaseModel):
    """
    Model representing a permission in the RBAC system.
    Permissions define specific actions that can be performed on resources.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['name']
        unique_together = ['code', 'organization']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the permission data"""
        if not self.name:
            raise ValidationError("Permission name cannot be empty")
        if not self.code:
            raise ValidationError("Permission code cannot be empty")
        if not re.match(r'^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$', self.code):
            raise ValidationError(
                "Permission code must be in format 'module.action' with lowercase letters, numbers, and underscores"
            )

    def get_cache_key(self):
        """Generate a unique cache key for this permission"""
        return f"permission:{self.id}:{self.code}"

    def has_permission(self, obj, action):
        """
        Check if this permission has the specified action on the given object.
        Permissions have full control over themselves.
        """
        if obj == self:
            return True
        return super().has_permission(obj, action)
