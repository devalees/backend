from rest_framework import permissions
from Apps.entity.models import TeamMember

class HasOrganizationPermission(permissions.BasePermission):
    """
    Custom permission to check if user belongs to the organization through team membership.
    """
    def has_permission(self, request, view):
        # Allow all users to access list and create views
        if view.action in ['list', 'create']:
            return True
        return True  # For now, allow all access. We'll implement proper checks later

    def has_object_permission(self, request, view, obj):
        # Check if user belongs to the organization through team membership
        return TeamMember.objects.filter(
            user=request.user,
            team__department__organization=obj.organization,
            is_active=True
        ).exists() 