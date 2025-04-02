"""
Permission caching functions for RBAC.
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from ..models import UserRole, RolePermission, RBACPermission, FieldPermission
from .cache_utils import (
    _get_user_permissions_cache_key,
    _get_field_permissions_cache_key,
    _get_role_permissions_cache_key,
    _invalidate_user_permissions,
    _invalidate_field_permissions
)

User = get_user_model()

def get_cached_user_permissions(user, model_class):
    """Get cached user permissions."""
    if not user or not user.is_authenticated:
        return set()

    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_user_permissions_cache_key(user.id, content_type.id)
    
    permissions = cache.get(cache_key)
    if permissions is None:
        # Get all roles for the user
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        role_ids = user_roles.values_list('role_id', flat=True)
        
        # Get all role permissions
        role_permissions = RolePermission.objects.filter(
            role_id__in=role_ids,
            permission__content_type=content_type
        ).select_related('permission')
        
        # Build permissions set
        permissions = {rp.permission.codename for rp in role_permissions}
        
        # Cache the permissions
        cache.set(cache_key, permissions, timeout=300)  # Cache for 5 minutes
    
    return permissions

def get_cached_field_permissions(user, model_class, field_name=None):
    """Get cached field permissions."""
    if not user or not user.is_authenticated:
        return {}

    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_field_permissions_cache_key(user.id, content_type.id, field_name)
    
    field_permissions = cache.get(cache_key)
    if field_permissions is None:
        # Get all roles for the user
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        role_ids = user_roles.values_list('role_id', flat=True)
        
        # Get all role permissions with field permissions
        role_permissions = RolePermission.objects.filter(
            role_id__in=role_ids,
            field_permission__content_type=content_type
        ).select_related('field_permission')
        
        if field_name:
            role_permissions = role_permissions.filter(
                field_permission__field_name=field_name
            )
        
        # Initialize field permissions with all model fields
        field_permissions = {}
        for field in model_class._meta.fields:
            field_permissions[field.name] = set()
        
        # Add permissions from role permissions
        for role_permission in role_permissions:
            if role_permission.field_permission:
                field = role_permission.field_permission.field_name
                permission_type = role_permission.field_permission.permission_type
                field_permissions[field].add(permission_type)
        
        # Cache the field permissions
        cache.set(cache_key, field_permissions, timeout=300)  # Cache for 5 minutes
    
    return field_permissions

def invalidate_permissions(user, model_class):
    """Invalidate all permission caches for a user and model."""
    _invalidate_user_permissions(user, model_class)

def invalidate_field_permissions(user, model_class, field_name=None):
    """Invalidate field permission caches for a user, model, and field."""
    _invalidate_field_permissions(user, model_class, field_name)

def invalidate_role_permissions(role, model_class):
    """Invalidate all permission caches for a role and model."""
    if not role or not model_class:
        return
        
    content_type = ContentType.objects.get_for_model(model_class)
    
    # Get all users with this role
    user_ids = UserRole.objects.filter(role=role, is_active=True).values_list('user_id', flat=True)
    
    # Invalidate permissions for each user
    for user_id in user_ids:
        _invalidate_user_permissions(user_id, model_class)
        _invalidate_field_permissions(user_id, model_class, None)  # Pass None to invalidate all field permissions

def invalidate_all_permissions():
    """Invalidate all permission caches."""
    cache.clear() 