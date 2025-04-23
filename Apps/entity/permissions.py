from rest_framework import permissions
from .models import Organization

class IsOrganizationMember(permissions.BasePermission):
    """
    Custom permission to only allow members of an organization to access its data.
    Superusers have full access to all operations.
    """
    def has_permission(self, request, view):
        # Superusers have full access
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        
        # For list and create actions, check if user is a member of any organization
        if view.action in ['list', 'create']:
            return Organization.objects.filter(
                departments__teams__members__user=request.user
            ).exists()
        return True

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_authenticated and request.user.is_superuser:
            return True
            
        # Check if the user is a member of the organization
        if isinstance(obj, Organization):
            return obj.departments.filter(
                teams__members__user=request.user
            ).exists()
        return False 