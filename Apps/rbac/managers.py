from django.db import models
from django.db.models import Q
from django.utils import timezone

class OrganizationIsolationManager(models.Manager):
    """
    Manager to enforce organization isolation at the query level.
    This manager ensures that queries are scoped to a specific organization.
    """
    
    def get_queryset(self):
        """
        Get the queryset with organization isolation applied.
        This method is called by the manager to get the queryset.
        """
        return super().get_queryset()
    
    def for_organization(self, organization):
        """
        Filter queryset to only include objects from the specified organization.
        
        Args:
            organization: The organization to filter by
            
        Returns:
            QuerySet: The filtered queryset
        """
        return self.get_queryset().filter(organization=organization)
    
    def for_user(self, user):
        """
        Filter queryset to only include objects from organizations the user belongs to.
        
        Args:
            user: The user to filter by
            
        Returns:
            QuerySet: The filtered queryset
        """
        # Get all organizations the user belongs to
        organizations = user.team_memberships.filter(
            is_active=True
        ).values_list(
            'team__department__organization', flat=True
        ).distinct()
        
        # Filter queryset to only include objects from those organizations
        return self.get_queryset().filter(organization__in=organizations)
    
    def active(self):
        """
        Filter queryset to only include active objects.
        
        Returns:
            QuerySet: The filtered queryset
        """
        return self.get_queryset().filter(is_active=True)
    
    def inactive(self):
        """
        Filter queryset to only include inactive objects.
        
        Returns:
            QuerySet: The filtered queryset
        """
        return self.get_queryset().filter(is_active=False)
    
    def with_permission(self, user, permission_code):
        """
        Filter queryset to only include objects the user has permission for.
        
        Args:
            user: The user to check permissions for
            permission_code: The permission code to check
            
        Returns:
            QuerySet: The filtered queryset
        """
        # Get all roles the user has with the specified permission
        roles = user.user_roles.filter(
            is_active=True,
            role__permissions__code=permission_code,
            role__permissions__is_active=True
        ).values_list('role', flat=True).distinct()
        
        # Filter queryset to only include objects from organizations the user has roles in
        return self.get_queryset().filter(
            organization__in=user.team_memberships.filter(
                is_active=True
            ).values_list(
                'team__department__organization', flat=True
            ).distinct()
        ) 