"""
Cache utility functions for RBAC permissions.
"""

from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

def _get_cache_key(user_id, model_class, permission_type=None, field_name=None):
    """Generate a cache key for permission checks"""
    content_type = ContentType.objects.get_for_model(model_class)
    if field_name:
        if field_name == 'all':
            return f'rbac:field_permissions:{user_id}:{content_type.id}'
        return f'rbac:field_permission:{user_id}:{content_type.id}:{field_name}'
    elif permission_type:
        return f'rbac:permission:{user_id}:{content_type.id}:{permission_type}'
    else:
        return f'rbac:permissions:{user_id}:{content_type.id}'

def _get_user_permissions_cache_key(user_id, content_type_id):
    """Get cache key for user permissions."""
    return f'rbac:permissions:{user_id}:{content_type_id}'

def _get_field_permissions_cache_key(user_id, content_type_id, field_name=None):
    """Get cache key for field permissions."""
    if field_name:
        return f'rbac:field_permission:{user_id}:{content_type_id}:{field_name}'
    return f'rbac:field_permissions:{user_id}:{content_type_id}'

def _get_role_permissions_cache_key(role_id, content_type_id):
    """Get cache key for role permissions."""
    return f'rbac:role_permissions:{role_id}:{content_type_id}'

def _invalidate_user_permissions(user_or_id, model_class):
    """Invalidate all permission caches for a user and model"""
    if not model_class:
        # If no model_class is provided, invalidate all permissions
        cache.clear()
        return

    # Get user ID from either user object or user ID
    user_id = user_or_id.id if hasattr(user_or_id, 'id') else user_or_id

    content_type = ContentType.objects.get_for_model(model_class)
    
    # Get all field names from the model
    field_names = [field.name for field in model_class._meta.fields if not field.name.startswith('_')]
    
    # Generate all possible cache keys
    cache_keys = [
        f'rbac:permissions:{user_id}:{content_type.id}',
        f'rbac:field_permissions:{user_id}:{content_type.id}'
    ]
    
    # Add permission-specific keys
    for permission_type in ['view', 'add', 'change', 'delete', 'view_user']:  # Add custom permission types
        cache_keys.append(f'rbac:permission:{user_id}:{content_type.id}:{permission_type}')
    
    # Add field-specific keys
    for field_name in field_names:
        for permission_type in ['view', 'add', 'change', 'delete']:
            cache_keys.append(f'rbac:field_permission:{user_id}:{content_type.id}:{field_name}:{permission_type}')
    
    # Delete all cache keys
    cache.delete_many(cache_keys)

def _invalidate_field_permissions(user, model_class, field_name):
    """Invalidate field permission caches for a user, model, and field"""
    # Get user ID from either user object or user ID
    user_id = user.id if hasattr(user, 'id') else user

    content_type = ContentType.objects.get_for_model(model_class)
    
    # Generate field-specific cache keys
    cache_keys = [
        f'rbac:field_permission:{user_id}:{content_type.id}:{field_name}',
        f'rbac:field_permissions:{user_id}:{content_type.id}'
    ]
    
    # Delete cache keys
    cache.delete_many(cache_keys)

def get_cached_user_permissions(user, model_class):
    """Get cached user permissions for a user and model"""
    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_user_permissions_cache_key(user.id, content_type.id)
    return cache.get(cache_key, set())

def get_cached_field_permissions(user, model_class, field_name=None):
    """Get cached field permissions for a user and model"""
    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_field_permissions_cache_key(user.id, content_type.id, field_name)
    return cache.get(cache_key, {})

def get_cached_role_permissions(role, model_class):
    """Get cached role permissions for a role and model"""
    content_type = ContentType.objects.get_for_model(model_class)
    cache_key = _get_role_permissions_cache_key(role.id, content_type.id)
    return cache.get(cache_key, set()) 