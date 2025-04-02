"""
Cache invalidation functions for RBAC permissions.
This module provides functions to invalidate permission caches when permissions change.
"""

from django.contrib.contenttypes.models import ContentType
from .cache_utils import _invalidate_user_permissions

def invalidate_role_permission_cache(role_permission):
    """Invalidate cache for all users with a role when a role permission changes."""
    if role_permission.permission:
        content_type = role_permission.permission.content_type
    else:
        content_type = role_permission.field_permission.content_type
    
    model_class = content_type.model_class()
    for user_role in role_permission.role.user_roles.all():
        _invalidate_user_permissions(user_role.user, model_class)

def invalidate_user_role_cache(user_role):
    """Invalidate cache for a user when their role changes."""
    for role_permission in user_role.role.role_permissions.all():
        if role_permission.permission:
            content_type = role_permission.permission.content_type
        else:
            content_type = role_permission.field_permission.content_type
        _invalidate_user_permissions(user_role.user, content_type.model_class())