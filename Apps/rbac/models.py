from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from Apps.entity.models import Organization
import re
from django.utils import timezone
from Apps.entity.models import TeamMember
from django.conf import settings
from .managers import OrganizationIsolationManager
from datetime import timedelta

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
    is_active = models.BooleanField(default=True)

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        abstract = True

    def clean(self):
        """Validate the model data"""
        if self.pk:  # Only check if this is an existing instance
            original = self.__class__.objects.get(pk=self.pk)
            if self.organization_id != original.organization_id:
                raise ValidationError("Cannot change organization of an existing instance")

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

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['name']
        unique_together = ['code', 'organization']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the permission data"""
        super().clean()
        
        if not self.name:
            raise ValidationError("Permission name cannot be empty")
        if not self.code:
            raise ValidationError("Permission code cannot be empty")
        if not re.match(r'^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$', self.code):
            raise ValidationError(
                "Permission code must be in format 'module.action' with lowercase letters, numbers, and underscores"
            )
            
        # Validate organization field
        if self.pk:  # Only check if this is an existing instance
            original = self.__class__.objects.get(pk=self.pk)
            if self.organization_id != original.organization_id:
                raise ValidationError("Cannot change organization of an existing instance")

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

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

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
            current_permissions = set(self.permissions.values_list('id', flat=True))
            if current_permissions != self._original_permissions:
                # Permissions have changed, invalidate cache
                self.invalidate_permission_cache()
            self._original_permissions = current_permissions

    def clean(self):
        """Validate the role data"""
        super().clean()
        if not self.name:
            raise ValidationError("Role name cannot be empty")
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\s]*$', self.name):
            raise ValidationError("Role name can only contain letters, numbers, spaces, and underscores")
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError("Parent role must belong to the same organization")

    def get_permission_cache_key(self, permission_code):
        """Generate cache key for permission checks"""
        return f"role_permission_{self.id}_{permission_code}"

    def has_permission(self, permission_code):
        """Check if the role has a specific permission"""
        if not self.is_active:
            return False
            
        # Check cache first
        cache_key = self.get_permission_cache_key(permission_code)
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
            
        # Check direct permissions
        has_perm = self.permissions.filter(
            code=permission_code,
            is_active=True
        ).exists()
        
        # If no direct permission, check parent role
        if not has_perm and self.parent and self.parent.is_active:
            has_perm = self.parent.has_permission(permission_code)
            
        # Cache the result
        cache.set(cache_key, has_perm, 300)  # Cache for 5 minutes
        return has_perm

    def invalidate_permission_cache(self, permission_code=None):
        """Invalidate the permission cache for this role"""
        if permission_code:
            # Invalidate specific permission cache
            cache_key = self.get_permission_cache_key(permission_code)
            cache.delete(cache_key)
        else:
            # If no specific permission code, invalidate all permission caches
            # This includes both direct permissions and inherited permissions
            for perm in Permission.objects.filter(organization=self.organization):
                cache_key = self.get_permission_cache_key(perm.code)
                cache.delete(cache_key)
        
        # Invalidate cache for child roles since they inherit permissions
        for child in self.children.all():
            child.invalidate_permission_cache(permission_code)

    def __str__(self):
        return self.name

    def deactivate(self):
        """Deactivate the role"""
        self.is_active = False
        self.save()
        self.invalidate_permission_cache()

    def activate(self):
        """Activate the role"""
        self.is_active = True
        self.save()
        self.invalidate_permission_cache()

    def m2m_changed(self, sender, instance, action, reverse, model, pk_set, **kwargs):
        """Handle M2M relationship changes"""
        if action in ["post_add", "post_remove", "post_clear"]:
            self.invalidate_permission_cache()

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

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

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
        
        # Check if the role has cross-organization permission
        has_cross_org_permission = self.role.permissions.filter(
            code='cross_org_access',
            is_active=True
        ).exists()
        
        # If the role has cross-organization permission, allow users from different organizations
        if not has_cross_org_permission and self.organization.id not in user_orgs:
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

class Resource(RBACBaseModel):
    """
    Model representing a resource in the RBAC system.
    Resources are objects that can be accessed by users with appropriate permissions.
    """
    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_resources'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        unique_together = ('name', 'resource_type', 'organization')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

    def clean(self):
        """Validate resource data"""
        super().clean()
        
        # Validate resource type
        valid_resource_types = ['document', 'folder', 'project', 'task', 'user', 'role', 'permission']
        if self.resource_type not in valid_resource_types:
            raise ValidationError({
                'resource_type': _('Invalid resource type. Must be one of: %(valid_types)s') % {
                    'valid_types': ', '.join(valid_resource_types)
                }
            })
        
        # Validate parent relationship
        if self.parent and self.parent.resource_type != 'folder':
            raise ValidationError({
                'parent': _('Parent resource must be of type "folder"')
            })
        
        # Validate parent organization
        if self.parent and self.parent.organization != self.organization:
            raise ValidationError({
                'parent': _('Parent resource must belong to the same organization')
            })

    def get_ancestors(self):
        """Get all ancestor resources"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant resources"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def grant_access(self, user, access_type):
        """
        Grant access to a user for this resource
        """
        from .models import ResourceAccess
        
        # Check if user belongs to the same organization
        user_teams = TeamMember.objects.filter(
            user=user,
            team__department__organization=self.organization,
            is_active=True
        )
        
        # If user is not in the same organization, check for cross-organization permission
        if not user_teams.exists():
            # Check if user has cross-organization permission
            has_cross_org_permission = UserRole.objects.filter(
                user=user,
                is_active=True,
                role__permissions__code='cross_org_access',
                role__permissions__is_active=True
            ).exists()
            
            if not has_cross_org_permission:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("User does not have cross-organization access permission")
        
        return ResourceAccess.objects.create(
            resource=self,
            user=user,
            access_type=access_type,
            organization=self.organization
        )

    def revoke_access(self, user, access_type=None):
        """
        Revoke access from a user for this resource
        """
        from .models import ResourceAccess
        query = ResourceAccess.objects.filter(
            resource=self,
            user=user,
            organization=self.organization,
            is_active=True
        )
        
        if access_type:
            query = query.filter(access_type=access_type)
        
        for access in query:
            access.deactivate()

    def has_access(self, user, access_type):
        """
        Check if a user has access to this resource
        """
        from .models import ResourceAccess
        
        # Check if user belongs to the same organization
        user_teams = TeamMember.objects.filter(
            user=user,
            team__department__organization=self.organization,
            is_active=True
        )
        if user_teams.exists():
            # For users in the same organization, check if they have explicit access
            # or if they have the 'admin' access type
            return ResourceAccess.objects.filter(
                resource=self,
                user=user,
                access_type__in=[access_type, 'admin'],
                organization=self.organization,
                is_active=True
            ).exists()
            
        # If not in the same organization, check for cross-organization permission and explicit access
        has_cross_org_permission = UserRole.objects.filter(
            user=user,
            is_active=True,
            role__permissions__code='cross_org_access',
            role__permissions__is_active=True
        ).exists()
        
        if not has_cross_org_permission:
            return False
            
        return ResourceAccess.objects.filter(
            resource=self,
            user=user,
            access_type=access_type,
            organization=self.organization,
            is_active=True
        ).exists()

class ResourceAccess(RBACBaseModel):
    """
    Model representing access to a resource by a user.
    Defines the type of access (read, write, etc.) and tracks access status.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='access_entries'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_access'
    )
    access_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        unique_together = ('resource', 'user', 'access_type', 'organization')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.resource.name} ({self.access_type})"

    def clean(self):
        """Validate resource access data"""
        if not self.resource:
            raise ValidationError("Resource is required")
        if not self.user:
            raise ValidationError("User is required")
        if not self.access_type:
            raise ValidationError("Access type is required")
        
        # Validate access type
        valid_access_types = ['read', 'write', 'delete', 'admin']
        if self.access_type not in valid_access_types:
            raise ValidationError({
                'access_type': f'Invalid access type. Must be one of: {", ".join(valid_access_types)}'
            })
        
        # Check if the resource belongs to the same organization
        if self.resource.organization != self.organization:
            raise ValidationError("Resource must belong to the same organization")
        
        # Check if the user belongs to the organization
        user_teams = TeamMember.objects.filter(
            user=self.user,
            team__department__organization=self.organization,
            is_active=True
        )
        if not user_teams.exists():
            raise ValidationError("User must belong to the organization")

    def deactivate(self):
        """Deactivate this access entry"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()

    def activate(self):
        """Activate this access entry"""
        self.is_active = True
        self.deactivated_at = None
        self.save()

class OrganizationContext(RBACBaseModel):
    """
    Model representing an organization context in the RBAC system.
    Organization contexts provide a way to group and organize resources within an organization.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        unique_together = ('name', 'organization')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def clean(self):
        """Validate the model data"""
        super().clean()
        
        # Validate name
        if not self.name:
            raise ValidationError("Name is required")
        
        # Check for duplicate names in the same organization
        query = OrganizationContext.objects.filter(
            name=self.name,
            organization=self.organization
        )
        if self.pk:
            query = query.exclude(pk=self.pk)
        
        if query.exists():
            raise ValidationError({
                'name': f"An organization context with the name '{self.name}' already exists in this organization"
            })
        
        # Validate parent
        if self.parent:
            if self.parent.organization != self.organization:
                raise ValidationError("Parent context must belong to the same organization")
            
            # Check for circular references
            if self.pk:  # Only check if this is an existing instance
                parent = self.parent
                while parent:
                    if parent.pk == self.pk:
                        raise ValidationError("Circular reference detected in organization context hierarchy")
                    parent = parent.parent

    def save(self, *args, **kwargs):
        """Override save to handle organization context changes"""
        super().save(*args, **kwargs)
        # Update the cache with the latest data
        self.cache_organization_data()

    def delete(self, *args, **kwargs):
        """Override delete to implement soft delete"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()
        # Invalidate organization cache after soft delete
        self.invalidate_organization_cache()

    def hard_delete(self):
        """Permanently delete the organization context"""
        super().delete()

    def deactivate(self):
        """Deactivate the organization context"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()

    def activate(self):
        """Activate the organization context"""
        self.is_active = True
        self.deactivated_at = None
        self.save()

    def get_ancestors(self):
        """Get all ancestors of this organization context"""
        ancestors = []
        parent = self.parent
        
        while parent:
            ancestors.append(parent)
            parent = parent.parent
        
        return ancestors

    def get_descendants(self):
        """Get all descendants of this organization context"""
        descendants = []
        children = self.children.all()
        
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        
        return descendants

    def get_all_children(self):
        """Get all direct children of this organization context"""
        return self.children.all()

    def get_all_parents(self):
        """Get all parents (ancestors) of this organization context"""
        parents = []
        current = self.parent
        while current:
            parents.append(current)
            current = current.parent
        return parents
    
    def get_organization_cache_key(self):
        """
        Generate a cache key for the organization data.
        The key is specific to this context to avoid conflicts.
        
        Returns:
            str: The cache key for the organization data
        """
        return f"rbac_organization_context_{self.id}_{self.organization.id}"
    
    def cache_organization_data(self, expiration=None):
        """
        Cache the organization data for this context.
        Only caches data relevant to this specific context.
        
        Args:
            expiration (int, optional): Cache expiration time in seconds. Defaults to None.
        """
        cache_key = self.get_organization_cache_key()
        
        # Prepare organization data for caching, focusing on context-specific data
        org_data = {
            'id': self.organization.id,
            'name': self.organization.name,
            'context_id': self.id,
            'context_name': self.name,
            'context_description': self.description,
            'context_is_active': self.is_active,
            'context_created_at': self.created_at.isoformat() if self.created_at else None,
            'context_updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add hierarchy information if available
        if self.parent:
            org_data['parent'] = {
                'id': self.parent.id,
                'name': self.parent.name,
                'context_id': self.parent.id
            }
        
        children = self.children.all()
        if children:
            org_data['children'] = [
                {
                    'id': child.id,
                    'name': child.name,
                    'context_id': child.id
                } for child in children
            ]
        
        # Cache the data
        cache.set(cache_key, org_data, expiration)
    
    def get_cached_organization(self):
        """
        Get the cached organization data for this context.
        
        Returns:
            dict: The cached organization data or None if not cached
        """
        cache_key = self.get_organization_cache_key()
        return cache.get(cache_key)
    
    def invalidate_organization_cache(self):
        """
        Invalidate the organization cache for this context.
        Only affects this specific context's cache.
        """
        cache_key = self.get_organization_cache_key()
        cache.delete(cache_key)
    
    def update_organization_cache(self):
        """
        Update the organization cache with the latest data.
        Only updates this specific context's cache.
        """
        self.cache_organization_data()
    
    @classmethod
    def cache_organization_data_bulk(cls, organization):
        """
        Cache organization data for all contexts in an organization.
        
        Args:
            organization: The organization to cache data for
        """
        contexts = cls.objects.filter(organization=organization)
        for context in contexts:
            context.cache_organization_data()

class OrganizationMonitor(RBACBaseModel):
    """
    Model for monitoring organization metrics and performance.
    Tracks various metrics related to organization usage, performance, and health.
    """
    organization_context = models.ForeignKey(
        OrganizationContext,
        on_delete=models.CASCADE,
        related_name='monitors'
    )
    metric_name = models.CharField(max_length=255)
    metric_value = models.FloatField()
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('counter', 'Counter'),
            ('gauge', 'Gauge'),
            ('histogram', 'Histogram'),
            ('summary', 'Summary')
        ]
    )
    timestamp = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization_context', 'metric_name', 'timestamp']),
            models.Index(fields=['organization_context', 'metric_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.organization_context.name} - {self.metric_name}: {self.metric_value}"

    def clean(self):
        """Validate the model data"""
        super().clean()
        if self.pk:  # Only check if this is an existing instance
            original = self.__class__.objects.get(pk=self.pk)
            if self.organization_context.organization_id != self.organization_id:
                raise ValidationError("Organization context must belong to the same organization")
        
        # Validate metric type
        valid_metric_types = dict(self._meta.get_field('metric_type').choices).keys()
        if self.metric_type not in valid_metric_types:
            raise ValueError(f"Invalid metric type. Must be one of: {', '.join(valid_metric_types)}")

    def save(self, *args, **kwargs):
        """Override save to ensure organization consistency"""
        # Ensure the organization is set from the organization context
        if self.organization_context and not self.organization_id:
            self.organization_id = self.organization_context.organization_id
        super().save(*args, **kwargs)
        # Cache the metrics after saving
        self.cache_metrics()

    def delete(self, *args, **kwargs):
        """Override delete to implement soft delete"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()
        # Invalidate metrics cache after soft delete
        self.invalidate_cache()

    def deactivate(self):
        """Deactivate the monitor"""
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.save()

    def activate(self):
        """Activate the monitor"""
        self.is_active = True
        self.deactivated_at = None
        self.save()

    @classmethod
    def get_latest_metrics(cls, organization_context):
        """Get the latest metrics for an organization context"""
        from django.db.models import Max, Subquery, OuterRef
        
        # Get the latest timestamp for each metric name
        latest_timestamps = cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            metric_name=OuterRef('metric_name')
        ).values('metric_name').annotate(
            max_timestamp=Max('timestamp')
        ).values('max_timestamp')
        
        # Get the metrics with the latest timestamps
        return cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            timestamp__in=Subquery(latest_timestamps)
        )

    @classmethod
    def get_metrics_by_time_range(cls, organization_context, start_time, end_time):
        """Get metrics for an organization context within a time range.
        
        Args:
            organization_context: The organization context to get metrics for
            start_time: The start time (exclusive)
            end_time: The end time (inclusive)
        """
        from django.utils import timezone
        
        # Convert times to timezone-aware if they're naive
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)
            
        # Get metrics within the time range (exclusive start, inclusive end)
        metrics = cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            timestamp__gt=start_time,  # Use gt to exclude metrics at exactly the start time
            timestamp__lte=end_time
        ).order_by('timestamp')
        
        return metrics

    @classmethod
    def get_metrics_by_type(cls, organization_context, metric_type):
        """Get metrics for an organization context by type"""
        return cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            metric_type=metric_type
        ).order_by('-timestamp')

    @classmethod
    def get_metrics_by_name(cls, organization_context, metric_name):
        """Get metrics for an organization context by name"""
        return cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            metric_name=metric_name
        ).order_by('-timestamp')

    @classmethod
    def aggregate_metrics(cls, organization_context, metric_name, aggregation_type='sum'):
        """Aggregate metrics for an organization context"""
        metrics = cls.objects.filter(
            organization_context=organization_context,
            is_active=True,
            metric_name=metric_name
        )
        
        if aggregation_type == 'sum':
            return metrics.aggregate(total=models.Sum('metric_value'))['total'] or 0
        elif aggregation_type == 'avg':
            return metrics.aggregate(avg=models.Avg('metric_value'))['avg'] or 0
        elif aggregation_type == 'min':
            return metrics.aggregate(min=models.Min('metric_value'))['min'] or 0
        elif aggregation_type == 'max':
            return metrics.aggregate(max=models.Max('metric_value'))['max'] or 0
        else:
            raise ValueError(f"Invalid aggregation type: {aggregation_type}")

    def get_metrics_cache_key(self):
        """Get the cache key for metrics"""
        return f"rbac_organization_monitor_{self.organization_context.id}_{self.metric_name}"

    def cache_metrics(self):
        """Cache the metrics data"""
        cache_key = self.get_metrics_cache_key()
        cache_data = {
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_type': self.metric_type,
            'timestamp': self.timestamp.isoformat(),
            'is_active': self.is_active
        }
        cache.set(cache_key, cache_data, timeout=3600)  # Cache for 1 hour

    @classmethod
    def get_cached_metrics(cls, organization_context):
        """Get cached metrics for an organization context"""
        # Get all active metrics for this context
        metrics = cls.objects.filter(
            organization_context=organization_context,
            is_active=True
        )
        
        # Get all cached data
        cached_data = []
        for metric in metrics:
            cache_key = metric.get_metrics_cache_key()
            data = cache.get(cache_key)
            if data:
                cached_data.append(data)
                
        return cached_data if cached_data else None

    @classmethod
    def invalidate_cache(cls, organization_context):
        """Invalidate the cache for an organization context"""
        # Get all active metrics for this context
        metrics = cls.objects.filter(
            organization_context=organization_context,
            is_active=True
        )
        
        # Delete cache for each metric
        for metric in metrics:
            cache_key = metric.get_metrics_cache_key()
            cache.delete(cache_key)

class Audit(RBACBaseModel):
    """
    Model for tracking audit logs in the RBAC system.
    Records all significant actions related to roles, permissions, and access control.
    """
    # Default retention period in days
    DEFAULT_RETENTION_PERIOD = 365
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.IntegerField()
    details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, default='success')
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    retention_period = models.IntegerField(default=DEFAULT_RETENTION_PERIOD, help_text="Number of days to retain this audit log")

    # Add the organization isolation manager
    objects = OrganizationIsolationManager()

    class Meta:
        app_label = 'rbac'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', 'action', 'timestamp']),
            models.Index(fields=['organization', 'resource_type', 'timestamp']),
            models.Index(fields=['organization', 'user', 'timestamp']),
        ]

    def __str__(self):
        return f"Audit: {self.action} on {self.resource_type} {self.resource_id}"

    def clean(self):
        """Validate the model data"""
        super().clean()
        if self.pk:  # Only check if this is an existing instance
            original = self.__class__.objects.get(pk=self.pk)
            if self.organization_id != original.organization_id:
                raise ValidationError("Cannot change organization of an existing audit entry")
        if self.retention_period < 1:
            raise ValidationError("Retention period must be at least 1 day")

    @classmethod
    def log_action(cls, organization, user, action, resource_type, resource_id, details=None, 
                  status='success', ip_address=None, user_agent=None, session_id=None, retention_period=365):
        """
        Create an audit log entry for an action.
        
        Args:
            organization: The organization the action belongs to
            user: The user who performed the action
            action: The action performed (e.g., 'create', 'update', 'delete')
            resource_type: The type of resource affected (e.g., 'role', 'permission')
            resource_id: The ID of the resource affected
            details: Additional details about the action (optional)
            status: The status of the action (default: 'success')
            ip_address: The IP address of the user (optional)
            user_agent: The user agent of the user's browser (optional)
            session_id: The session ID of the user (optional)
            retention_period: Number of days to retain this audit log (default: 365)
            
        Returns:
            The created audit log entry
        """
        if details is None:
            details = {}
            
        return cls.objects.create(
            organization=organization,
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            retention_period=retention_period
        )

    @classmethod
    def get_audit_logs(cls, organization, resource_type=None, resource_id=None, 
                      user=None, action=None, start_date=None, end_date=None, 
                      status=None, limit=100):
        """
        Get audit logs for an organization with optional filters.
        
        Args:
            organization: The organization to get audit logs for
            resource_type: Filter by resource type (optional)
            resource_id: Filter by resource ID (optional)
            user: Filter by user (optional)
            action: Filter by action (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            status: Filter by status (optional)
            limit: Maximum number of logs to return (default: 100)
            
        Returns:
            QuerySet of audit logs matching the filters
        """
        query = cls.objects.filter(organization=organization)
        
        if resource_type:
            query = query.filter(resource_type=resource_type)
        if resource_id:
            query = query.filter(resource_id=resource_id)
        if user:
            query = query.filter(user=user)
        if action:
            query = query.filter(action=action)
        if start_date:
            query = query.filter(timestamp__gte=start_date)
        if end_date:
            query = query.filter(timestamp__lte=end_date)
        if status:
            query = query.filter(status=status)
            
        return query.order_by('-timestamp')[:limit]

    @classmethod
    def cleanup_expired_audits(cls, organization):
        """
        Clean up expired audit logs for an organization based on their retention period.
        
        Args:
            organization: The organization to clean up audit logs for
            
        Returns:
            The number of audit logs deleted
        """
        now = timezone.now()
        expired_audits = cls.objects.filter(organization=organization)
        
        # Calculate the cutoff date for each audit based on its retention period
        expired_ids = []
        for audit in expired_audits:
            cutoff_date = now - timedelta(days=audit.retention_period)
            if audit.timestamp < cutoff_date:
                expired_ids.append(audit.id)
        
        # Delete the expired audits
        if expired_ids:
            cls.objects.filter(id__in=expired_ids).delete()
            return len(expired_ids)
        
        return 0

    @classmethod
    def generate_compliance_report(cls, organization, report_type='comprehensive', 
                                 start_date=None, end_date=None):
        """
        Generate a compliance report based on audit logs.
        
        Args:
            organization: The organization to generate the report for
            report_type: The type of report to generate (default: 'comprehensive')
                Options: 'role_changes', 'permission_changes', 'user_role_assignments', 
                'resource_access', 'comprehensive'
            start_date: The start date for the report (optional)
            end_date: The end date for the report (optional)
            
        Returns:
            A dictionary containing the report data
        """
        from django.utils import timezone
        
        # Set default date range if not provided
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)  # Default to last 30 days
            
        # Validate date range
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
            
        # Initialize report
        report = {
            'organization': organization.id,
            'start_date': start_date,
            'end_date': end_date,
            'generated_at': timezone.now(),
            'report_type': report_type
        }
        
        # Get audit logs for the date range
        audit_logs = cls.objects.filter(
            organization=organization,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        # Generate report based on type
        if report_type == 'role_changes' or report_type == 'comprehensive':
            role_changes = audit_logs.filter(
                resource_type='role',
                action__in=['role_created', 'role_updated', 'role_deleted', 'role_activated', 'role_deactivated']
            )
            report['role_changes'] = [
                {
                    'id': log.id,
                    'action': log.action,
                    'resource_id': log.resource_id,
                    'user_id': log.user_id,
                    'timestamp': log.timestamp,
                    'details': log.details,
                    'status': log.status
                }
                for log in role_changes
            ]
            
        if report_type == 'permission_changes' or report_type == 'comprehensive':
            permission_changes = audit_logs.filter(
                resource_type='permission',
                action__in=['permission_created', 'permission_updated', 'permission_deleted']
            )
            report['permission_changes'] = [
                {
                    'id': log.id,
                    'action': log.action,
                    'resource_id': log.resource_id,
                    'user_id': log.user_id,
                    'timestamp': log.timestamp,
                    'details': log.details,
                    'status': log.status
                }
                for log in permission_changes
            ]
            
        if report_type == 'user_role_assignments' or report_type == 'comprehensive':
            user_role_assignments = audit_logs.filter(
                resource_type='user_role',
                action__in=['user_role_assigned', 'user_role_revoked', 'user_role_delegated']
            )
            report['user_role_assignments'] = [
                {
                    'id': log.id,
                    'action': log.action,
                    'resource_id': log.resource_id,
                    'user_id': log.user_id,
                    'timestamp': log.timestamp,
                    'details': log.details,
                    'status': log.status
                }
                for log in user_role_assignments
            ]
            
        if report_type == 'resource_access' or report_type == 'comprehensive':
            resource_access = audit_logs.filter(
                resource_type='resource_access',
                action__in=['resource_access_granted', 'resource_access_revoked']
            )
            report['resource_access'] = [
                {
                    'id': log.id,
                    'action': log.action,
                    'resource_id': log.resource_id,
                    'user_id': log.user_id,
                    'timestamp': log.timestamp,
                    'details': log.details,
                    'status': log.status
                }
                for log in resource_access
            ]
            
        # Validate report type
        if report_type not in ['role_changes', 'permission_changes', 'user_role_assignments', 
                              'resource_access', 'comprehensive']:
            raise ValueError(f"Invalid report type: {report_type}")
            
        return report
