from rest_framework import permissions
from django.db.models import Q

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Superusers have full access to all operations.
    """

    def has_permission(self, request, view):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # Allow GET, HEAD, OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow POST requests (create)
        if request.method == 'POST':
            return True
        
        return False

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

class IsOrganizationMember(permissions.BasePermission):
    """
    Custom permission to only allow members of an organization to access its objects.
    Superusers have full access to all operations.
    """

    def has_permission(self, request, view):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # For list and create actions, check if user is a member of any organization
        if view.action in ['list', 'create']:
            # Get organizations where user is a member of any team
            user_organizations = request.user.team_memberships.values_list(
                'team__department__organization', flat=True
            ).distinct()
            return user_organizations.exists()
        return True

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # Get the organization from the object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'project'):
            organization = obj.project.organization
        else:
            return False

        # Check if user is a member of any team in the organization
        return request.user.team_memberships.filter(
            team__department__organization=organization
        ).exists() 