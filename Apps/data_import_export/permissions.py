from rest_framework import permissions


class IsConfigOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a config to edit it.
    """

    def has_permission(self, request, view):
        # Allow any authenticated user to access the viewset
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user


class CanPerformImportExport(permissions.BasePermission):
    """
    Custom permission to check if user can perform import/export operations.
    """

    def has_permission(self, request, view):
        # For testing purposes, allow all authenticated users
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For testing purposes, allow all authenticated users
        return request.user.is_authenticated


class CanViewLogs(permissions.BasePermission):
    """
    Custom permission to check if user can view import/export logs.
    """

    def has_permission(self, request, view):
        # For testing purposes, allow all authenticated users
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For testing purposes, allow all authenticated users
        return request.user.is_authenticated