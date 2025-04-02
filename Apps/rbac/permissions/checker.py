"""
Permission checking functions that wrap the utility functions.
This module provides the public API for permission checking.
"""

from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from .cache_utils import _get_cache_key, _invalidate_user_permissions
from .utils import check_permission, get_user_perms, get_field_perms, check_role

User = get_user_model()

def has_permission(user, permission_type, model, field=None):
    """Check if a user has a specific permission on a model."""
    return check_permission(user, permission_type, model, field)

def get_user_permissions(user, model):
    """Get all permissions a user has on a model."""
    return get_user_perms(user, model)

def get_field_permissions(user, model):
    """Get field-level permissions for a user on a model."""
    return get_field_perms(user, model)

def has_role(user, role_name):
    """Check if a user has a specific role."""
    return check_role(user, role_name)

__all__ = ['has_permission', 'get_user_permissions', 'get_field_permissions', 'has_role'] 