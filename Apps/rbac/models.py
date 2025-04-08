from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from Apps.entity.models import Organization
import re
from django.utils import timezone
from Apps.entity.models import TeamMember
from django.conf import settings

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
            cache.delete(f"rbac_permission_{self.__class__.__name__}_{self.id}_{user.id}_*")
        else:
            # Invalidate all users' permissions
            cache.delete(f"rbac_permission_{self.__class__.__name__}_{self.id}_*_*")

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

class Role(RBACBaseModel):
    """
    Role model for implementing role-based access control.
    Supports role hierarchy and permission inheritance.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)

    class Meta:
        app_label = 'rbac'
        unique_together = ('name', 'organization')
        ordering = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original permissions for change detection
        self._original_permissions = set()
        if self.pk:
            self._original_permissions = set(self.permissions.values_list('id', flat=True))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Update original permissions after save
        if self.pk:
            self._original_permissions = set(self.permissions.values_list('id', flat=True))

    def get_permission_cache_key(self, permission_code):
        """Generate cache key for permission checks"""
        return f"role_permission_{self.id}_{permission_code}"

    def add_permission(self, permission):
        """Add a permission to the role"""
        if isinstance(permission, str):
            # If permission is a string (code), get the Permission object
            permission = Permission.objects.get(code=permission, organization=self.organization)
        
        if permission.organization != self.organization:
            raise ValidationError("Permission must belong to the same organization")
        
        self.permissions.add(permission)
        self.invalidate_permission_cache(permission.code)

    def remove_permission(self, permission):
        """Remove a permission from the role"""
        if isinstance(permission, str):
            try:
                # If permission is a string (code), get the Permission object
                permission = Permission.objects.get(code=permission, organization=self.organization)
            except Permission.DoesNotExist:
                return  # If permission doesn't exist, nothing to remove
        
        # Remove the permission
        self.permissions.remove(permission)
        
        # Invalidate cache for this permission
        self.invalidate_permission_cache(permission.code)
        
        # Also invalidate cache for all child roles recursively
        for child in self.children.all():
            child.invalidate_permission_cache(permission.code)

    def has_permission(self, permission_code):
        """Check if the role has a specific permission"""
        if not self.is_active:
            return False

        cache_key = self.get_permission_cache_key(permission_code)
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        # Check if permission exists and is active
        try:
            permission = Permission.objects.get(code=permission_code, organization=self.organization)
            if not permission.is_active:
                cache.set(cache_key, False, timeout=300)
                return False

            # Check direct permissions first
            has_direct_permission = self.permissions.filter(
                code=permission_code,
                is_active=True
            ).exists()

            if has_direct_permission:
                cache.set(cache_key, True, timeout=300)
                return True

            # Check parent role if exists and is active
            if self.parent and self.parent.is_active:
                has_parent_permission = self.parent.has_permission(permission_code)
                cache.set(cache_key, has_parent_permission, timeout=300)
                return has_parent_permission

            cache.set(cache_key, False, timeout=300)
            return False

        except Permission.DoesNotExist:
            cache.set(cache_key, False, timeout=300)
            return False

    def invalidate_permission_cache(self, permission_code=None):
        """Invalidate permission cache for this role"""
        if permission_code:
            # Invalidate specific permission
            cache.delete(self.get_permission_cache_key(permission_code))
        else:
            # Invalidate all permissions
            for permission in self.permissions.all():
                cache.delete(self.get_permission_cache_key(permission.code))

    def __str__(self):
        return self.name

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

    def deactivate(self):
        """Deactivate the role"""
        self.is_active = False
        self.save()

    def activate(self):
        """Activate the role"""
        self.is_active = True
        self.save()

class UserRole(RBACBaseModel):
    """Model representing a role assignment to a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    delegated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_roles')
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    is_delegated = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        app_label = 'rbac'
        unique_together = ['user', 'role', 'organization']
        ordering = ['-created_at']

    def clean(self):
        """Validate the user role assignment"""
        super().clean()
        
        # Check if user belongs to the organization through team membership
        user_orgs = set(
            TeamMember.objects.filter(
                user=self.user,
                team__department__organization=self.organization,
                is_active=True
            ).values_list('team__department__organization', flat=True)
        )
        
        if self.organization.id not in user_orgs:
            raise ValidationError("User must belong to the organization through an active team membership")

        # Check if role belongs to the organization
        if self.role.organization != self.organization:
            raise ValidationError("Role must belong to the same organization")
        
        # Validate assigned_by
        if self.assigned_by and not TeamMember.objects.filter(
            user=self.assigned_by,
            team__department__organization=self.organization,
            is_active=True
        ).exists():
            raise ValidationError("Assigning user must belong to the same organization")

        # Validate delegated_by
        if self.delegated_by:
            if self.delegated_by.organization != self.organization:
                raise ValidationError("Delegating role must belong to the same organization")
            self.is_delegated = True
        else:
            self.is_delegated = False

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def deactivate(self):
        """Deactivate the user role assignment"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()
        self.invalidate_permission_cache()

    def activate(self):
        """Activate the user role assignment"""
        self.is_active = True
        self.deactivated_at = None
        self.save()
        self.invalidate_permission_cache()

    def has_permission(self, permission):
        """
        Check if the user has a specific permission through this role
        Uses caching to improve performance
        """
        if not self.is_active:
            return False

        cache_key = self.get_permission_cache_key(self.user, permission)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result

        has_perm = self.role.has_permission(permission)
        cache.set(cache_key, has_perm, timeout=300)  # Cache for 5 minutes
        return has_perm

    def has_higher_priority_than(self, other_user_role):
        """
        Determine if this role assignment has higher priority than another
        Used for conflict resolution
        """
        if not self.is_active or not other_user_role.is_active:
            return False
        
        # Delegated roles have lower priority
        if self.is_delegated and not other_user_role.is_delegated:
            return False
        if not self.is_delegated and other_user_role.is_delegated:
            return True
        
        # More specific roles have higher priority
        if self.role.parent == other_user_role.role:
            return True
        if other_user_role.role.parent == self.role:
            return False
        
        # If no clear hierarchy, newer assignments have higher priority
        return self.created_at > other_user_role.created_at

    def __str__(self):
        return f"{self.user.username} - {self.role.name} ({self.organization.name})"
