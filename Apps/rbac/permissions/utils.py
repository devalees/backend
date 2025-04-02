"""
Utility functions for RBAC permissions that don't depend on models.
This module should not import any models to avoid circular dependencies.
"""

from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Q
from .cache_utils import _get_cache_key, _invalidate_user_permissions, _invalidate_field_permissions

User = get_user_model()

def check_permission(user, permission_type, model, field=None):
    """Check if a user has a specific permission on a model."""
    if not user or not user.is_authenticated:
        return False
        
    cache_key = _get_cache_key(user.id, model, permission_type, field)
    result = cache.get(cache_key)
    
    if result is None:
        # Get the content type for the model
        content_type = ContentType.objects.get_for_model(model)
        
        # Build the base query
        query = Q(
            role__user_roles__user=user,
            permission__content_type=content_type,
            permission__codename=permission_type
        )
        
        # Add field permission check if field is specified
        if field:
            query &= Q(
                field_permission__field_name=field,
                field_permission__permission_type=permission_type
            )
        
        # Import RolePermission here to avoid circular imports
        from ..models import RolePermission
        
        # Check if any of the user's roles have the permission
        result = RolePermission.objects.filter(query).exists()
        
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
    
    return result

def get_user_perms(user, model):
    """Get all permissions a user has on a model."""
    if not user or not user.is_authenticated:
        return set()
        
    cache_key = _get_cache_key(user.id, model)
    result = cache.get(cache_key)
    
    if result is None:
        # Import RolePermission here to avoid circular imports
        from ..models import RolePermission
        
        # Get all permissions for the user's roles in a single query
        result = set(RolePermission.objects.filter(
            role__user_roles__user=user,
            permission__content_type=ContentType.objects.get_for_model(model)
        ).values_list('permission__codename', flat=True))
        
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
    
    return result

def get_field_perms(user, model):
    """Get field-level permissions for a user on a model."""
    if not user or not user.is_authenticated:
        return {}
        
    cache_key = _get_cache_key(user.id, model, field_name='all')
    result = cache.get(cache_key)
    
    if result is None:
        # Import RolePermission here to avoid circular imports
        from ..models import RolePermission
        
        # Get all field permissions for the user's roles in a single query
        field_perms = RolePermission.objects.filter(
            role__user_roles__user=user,
            field_permission__content_type=ContentType.objects.get_for_model(model)
        ).values_list('field_permission__field_name', 'field_permission__permission_type')
        
        # Convert to dictionary format
        result = {}
        for field_name, perm_type in field_perms:
            if field_name not in result:
                result[field_name] = set()
            result[field_name].add(perm_type)
        
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
    
    return result

def check_role(user, role_name):
    """Check if a user has a specific role."""
    if not user or not user.is_authenticated:
        return False
        
    cache_key = f'rbac:role:{user.id}:{role_name}'
    result = cache.get(cache_key)
    
    if result is None:
        # Import UserRole here to avoid circular imports
        from ..models import UserRole
        
        # Check if user has the role
        result = UserRole.objects.filter(
            user=user,
            role__name=role_name
        ).exists()
        
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
    
    return result

def invalidate_permissions(user, model):
    """Invalidate all permission caches for a user and model."""
    _invalidate_user_permissions(user.id, model)

def invalidate_field_permissions(user, model, field_name):
    """Invalidate field permission caches for a user, model, and field."""
    _invalidate_field_permissions(user.id, model, field_name)

__all__ = ['check_permission', 'get_user_perms', 'get_field_perms', 'check_role', 'invalidate_permissions', 'invalidate_field_permissions'] 