"""
Permission decorators for RBAC.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from .caching import get_cached_user_permissions, get_cached_field_permissions

def has_permission(permission_codename):
    """
    Decorator to check if a user has a specific permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
                raise PermissionDenied("User must be authenticated.")
            
            model = kwargs.get('model', None)
            if not model:
                raise ValueError("Model must be specified in kwargs.")
            
            permissions = get_cached_user_permissions(request.user, model)
            if permission_codename not in permissions:
                raise PermissionDenied(f"User does not have permission: {permission_codename}")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def has_field_permission(permission_type):
    """
    Decorator to check if a user has permission on a specific field.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
                raise PermissionDenied("User must be authenticated.")
            
            model = kwargs.get('model', None)
            field_name = kwargs.get('field_name', None)
            
            if not model or not field_name:
                raise ValueError("Model and field_name must be specified in kwargs.")
            
            field_permissions = get_cached_field_permissions(request.user, model)
            if field_name not in field_permissions or permission_type not in field_permissions[field_name]:
                raise PermissionDenied(f"User does not have {permission_type} permission on field: {field_name}")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_permission(permission_codename):
    """
    Decorator to require a specific permission.
    """
    return has_permission(permission_codename)

def require_field_permission(permission_type):
    """
    Decorator to require a specific field permission.
    """
    return has_field_permission(permission_type)

def has_role(role_name):
    """
    Decorator to check if a user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
                raise PermissionDenied("User must be authenticated.")
            
            if not request.user.roles.filter(name=role_name).exists():
                raise PermissionDenied(f"User does not have role: {role_name}")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_role(role_name):
    """
    Decorator to require a specific role.
    """
    return has_role(role_name)

__all__ = ['require_permission', 'require_role', 'has_permission', 'has_field_permission', 'has_role'] 