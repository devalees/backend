"""
Cache utilities for RBAC.
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()

def invalidate_permissions_cache(role):
    """
    Invalidate permissions cache for all users with the given role.
    """
    # Get all users with this role
    users = User.objects.filter(user_roles__role=role)
    
    # Invalidate user permissions cache
    for user in users:
        cache.delete(f'user_permissions_{user.id}')
        
    # Invalidate field permissions cache for all models
    for model in role.role_permissions.filter(
        field_permission__isnull=False
    ).values_list('field_permission__content_type__model', flat=True).distinct():
        for user in users:
            cache.delete(f'field_permissions_{user.id}_{model}')
            
    # Invalidate field permissions cache for models with regular permissions
    for model in role.role_permissions.filter(
        permission__isnull=False
    ).values_list('permission__content_type__model', flat=True).distinct():
        for user in users:
            cache.delete(f'field_permissions_{user.id}_{model}') 