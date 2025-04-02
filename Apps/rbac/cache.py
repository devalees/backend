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
    
    # Invalidate cache for each user
    for user in users:
        cache_key = f'user_permissions_{user.id}'
        cache.delete(cache_key) 