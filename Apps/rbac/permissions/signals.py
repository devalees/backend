"""
Signal handlers for RBAC permissions.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q

from ..models import (
    RBACPermission,
    FieldPermission,
    RolePermission,
    UserRole
)
from .cache_invalidation import (
    invalidate_role_permission_cache,
    invalidate_user_role_cache
)
from .cache_utils import _invalidate_user_permissions

@receiver([post_save, post_delete], sender=RBACPermission)
def invalidate_permission_cache(sender, instance, **kwargs):
    """Invalidate cache when permissions change"""
    _invalidate_user_permissions(None, instance.content_type.model_class())

@receiver([post_save, post_delete])
def invalidate_role_permission_cache(sender, instance, **kwargs):
    """Invalidate cache when role permissions change"""
    # Import here to avoid circular imports
    if sender == RolePermission:
        if instance.permission:
            _invalidate_user_permissions(None, instance.permission.content_type.model_class())
        elif instance.field_permission:
            _invalidate_user_permissions(None, instance.field_permission.content_type.model_class())

@receiver([post_save, post_delete])
def invalidate_user_role_cache(sender, instance, **kwargs):
    """Invalidate cache when user roles change"""
    # Import here to avoid circular imports
    if sender == UserRole:
        # Get all content types that have permissions
        content_types = ContentType.objects.filter(
            Q(rbacpermission__isnull=False) | Q(fieldpermission__isnull=False)
        ).distinct()
        
        # Invalidate cache for each content type
        for content_type in content_types:
            _invalidate_user_permissions(instance.user.id, content_type.model_class())