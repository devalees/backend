"""
Permission mixins for RBAC.
"""

from django.core.exceptions import PermissionDenied
from .caching import get_cached_user_permissions, get_cached_field_permissions

class RBACPermissionMixin:
    """
    Mixin to add RBAC permission checking to views.
    """
    def has_permission(self, permission_codename, model_class):
        """
        Check if user has a specific permission.
        """
        user = getattr(self, 'user', None)
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return False
        
        if not model_class:
            return False
        
        permissions = get_cached_user_permissions(user, model_class)
        return permission_codename in permissions
    
    def has_field_permission(self, user, field_name, permission_type):
        """
        Check if user has permission on a specific field.
        """
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return False
        
        model = getattr(self, 'model', None)
        if not model:
            return False
        
        field_permissions = get_cached_field_permissions(user, model)
        return field_name in field_permissions and permission_type in field_permissions[field_name]
    
    def check_permission(self, permission_codename, model_class):
        """
        Check permission and raise PermissionDenied if not allowed.
        """
        if not self.has_permission(permission_codename, model_class):
            raise PermissionDenied(f"User does not have permission: {permission_codename}")
    
    def check_field_permission(self, user, field_name, permission_type):
        """
        Check field permission and raise PermissionDenied if not allowed.
        """
        if not self.has_field_permission(user, field_name, permission_type):
            raise PermissionDenied(f"User does not have {permission_type} permission on field: {field_name}")
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to check permissions before handling the request.
        """
        # Check model-level permission based on request method
        method_permission_map = {
            'GET': 'view',
            'POST': 'add',
            'PUT': 'change',
            'PATCH': 'change',
            'DELETE': 'delete'
        }
        
        permission = method_permission_map.get(request.method)
        if permission:
            self.check_permission(permission, self.model)
        
        return super().dispatch(request, *args, **kwargs) 