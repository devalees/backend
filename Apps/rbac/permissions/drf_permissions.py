from rest_framework import permissions
from django.contrib.auth import get_user_model
from .checker import has_role

User = get_user_model()

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        # Write permissions are only allowed to admin users
        return bool(request.user and request.user.is_staff)

class CanManageRoles(permissions.BasePermission):
    """
    Custom permission to only allow users with specific roles to manage roles.
    """
    def has_permission(self, request, view):
        # Allow all operations for admin users
        if request.user and request.user.is_staff:
            return True
            
        # For read operations, user must have any role
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated and has_role(request.user, 'role_viewer'))
            
        # For write operations, user must have admin role
        return bool(request.user and request.user.is_authenticated and has_role(request.user, 'role_admin'))
    
    def has_object_permission(self, request, view, obj):
        # Admin users can manage all objects
        if request.user and request.user.is_staff:
            return True
            
        # For read operations, user must have any role
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated and has_role(request.user, 'role_viewer'))
            
        # For write operations, user must have admin role
        return bool(request.user and request.user.is_authenticated and has_role(request.user, 'role_admin'))

__all__ = ['IsAdminOrReadOnly', 'CanManageRoles'] 