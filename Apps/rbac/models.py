from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from Apps.entity.models import Organization

class RBACBaseModel(models.Model):
    """
    Abstract base model for RBAC implementation with organization isolation support.
    Provides common fields and methods for all RBAC-related models.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='%(class)s_related'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    class Meta:
        abstract = True

    def get_permission_cache_key(self, user, permission):
        """Generate cache key for permission checks"""
        return f"rbac_permission_{self.__class__.__name__}_{self.id}_{user.id}_{permission}"

    def has_permission(self, user, permission):
        """
        Check if user has specific permission on this object
        Uses caching to improve performance
        """
        cache_key = self.get_permission_cache_key(user, permission)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result

        # Implement permission check logic here
        # This is a placeholder - actual implementation will be added in subsequent steps
        result = False
        
        # Cache the result
        cache.set(cache_key, result, timeout=300)  # Cache for 5 minutes
        return result

    def get_field_permission(self, user, field_name):
        """
        Check if user has permission to access specific field
        """
        # Implement field-level permission check logic here
        # This is a placeholder - actual implementation will be added in subsequent steps
        return True

    def invalidate_permission_cache(self, user=None):
        """
        Invalidate permission cache for this object
        """
        if user:
            # Invalidate specific user's permissions
            cache.delete_pattern(f"rbac_permission_{self.__class__.__name__}_{self.id}_{user.id}_*")
        else:
            # Invalidate all users' permissions
            cache.delete_pattern(f"rbac_permission_{self.__class__.__name__}_{self.id}_*_*")
