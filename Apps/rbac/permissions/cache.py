from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

def _get_cache_key(user_id, model, permission_type=None, field_name=None):
    """Generate a cache key for permission checks"""
    content_type = ContentType.objects.get_for_model(model)
    if field_name:
        return f'rbac:field_permission:{user_id}:{content_type.id}:{field_name}'
    elif permission_type:
        return f'rbac:permission:{user_id}:{content_type.id}:{permission_type}'
    else:
        return f'rbac:permissions:{user_id}:{content_type.id}'

def _invalidate_user_permissions(user_id, model):
    """Invalidate all permission caches for a user and model"""
    content_type = ContentType.objects.get_for_model(model)
    cache_keys = [
        f'rbac:permissions:{user_id}:{content_type.id}',
        f'rbac:field_permissions:{user_id}:{content_type.id}'
    ]
    cache.delete_many(cache_keys)

__all__ = ['_get_cache_key', '_invalidate_user_permissions'] 