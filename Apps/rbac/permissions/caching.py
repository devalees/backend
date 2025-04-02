"""
Permission caching functions for RBAC.
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import UserRole, RolePermission, RBACPermission, FieldPermission

User = get_user_model()

def _get_user_permissions_cache_key(user_id, content_type_id):
    """Get cache key for user permissions."""
    return f'user_permissions_{user_id}_{content_type_id}'

def _get_field_permissions_cache_key(user_id, content_type_id, field_name=None):
    """Get cache key for field permissions."""
    key = f'field_permissions_{user_id}_{content_type_id}'
    if field_name:
        key += f'_{field_name}'
    return key

def get_cached_user_permissions(user, model_class):
    """Get cached user permissions."""
    if not user or not user.is_authenticated:
        return set()

    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_user_permissions_cache_key(user.id, content_type.id)
    
    permissions = cache.get(cache_key)
    if permissions is None:
        # Get all roles for the user
        user_roles = UserRole.objects.filter(user=user)
        role_ids = user_roles.values_list('role_id', flat=True)
        
        # Get all role permissions with model permissions
        role_permissions = RolePermission.objects.filter(
            role_id__in=role_ids,
            permission__isnull=False
        )
        
        # Build permissions set
        permissions = set(role_permissions.values_list('permission__codename', flat=True))
        
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
        user_roles = UserRole.objects.filter(user=user)
        role_ids = user_roles.values_list('role_id', flat=True)
        
        # Get all role permissions with field permissions
        role_permissions = RolePermission.objects.filter(
            role_id__in=role_ids,
            field_permission__isnull=False
        )
        
        if field_name:
            role_permissions = role_permissions.filter(
                field_permission__field_name=field_name
            )
        
        # Build field permissions dictionary
        field_permissions = {}
        for role_permission in role_permissions:
            field_name = role_permission.field_permission.field_name
            permission_type = role_permission.field_permission.permission_type
            
            if field_name not in field_permissions:
                field_permissions[field_name] = set()
            field_permissions[field_name].add(permission_type)
        
        # Cache the field permissions
        cache.set(cache_key, field_permissions, timeout=300)  # Cache for 5 minutes
    
    return field_permissions

def invalidate_permissions(user, model_class):
    """Invalidate cached permissions for a user and model."""
    if not user or not model_class:
        return
        
    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_user_permissions_cache_key(user.id, content_type.id)
    cache.delete(cache_key)

def invalidate_field_permissions(user, model_class, field_name=None):
    """Invalidate cached field permissions for a user and model."""
    if not user or not model_class:
        return
        
    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_field_permissions_cache_key(user.id, content_type.id, field_name)
    cache.delete(cache_key)

def invalidate_role_permissions(role):
    """Invalidate permissions cache for all users with a role."""
    if not role:
        return
    
    # Get all users with this role
    user_ids = UserRole.objects.filter(role=role).values_list('user_id', flat=True)
    
    # Invalidate permissions for each user
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            # Invalidate all content types
            for content_type in ContentType.objects.all():
                cache_key = _get_user_permissions_cache_key(user_id, content_type.id)
                cache.delete(cache_key)
                cache_key = _get_field_permissions_cache_key(user_id, content_type.id)
                cache.delete(cache_key)
        except User.DoesNotExist:
            continue

def invalidate_all_permissions():
    """Invalidate all permission caches."""
    cache.clear() 