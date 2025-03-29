from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to admins
        return request.user and request.user.is_staff

class CanManageRoles(permissions.BasePermission):
    """
    Custom permission to only allow users with specific roles to manage roles.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admins can do everything
        if request.user.is_staff:
            return True

        # For read operations, check if user has any role
        if request.method in permissions.SAFE_METHODS:
            return request.user.user_roles.exists()

        # For write operations, check if user has admin role
        return request.user.user_roles.filter(role__name='admin').exists()

    def has_object_permission(self, request, view, obj):
        # Admins can do everything
        if request.user.is_staff:
            return True

        # For read operations, check if user has access to the object
        if request.method in permissions.SAFE_METHODS:
            if isinstance(obj, User):
                return obj == request.user
            return True

        # For write operations, check if user has admin role
        return request.user.user_roles.filter(role__name='admin').exists() 