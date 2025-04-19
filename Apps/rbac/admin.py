from django.contrib import admin
from django.db.models import Q
from django.contrib.admin.utils import flatten_fieldsets
from django.core.exceptions import PermissionDenied

class OrganizationIsolationAdminMixin:
    """
    Admin mixin that enforces organization isolation in the Django admin interface.
    
    This mixin ensures that users can only see and manage records from their own organization.
    """
    
    def get_queryset(self, request):
        """
        Override get_queryset to filter by organization if the user has one associated.
        """
        qs = super().get_queryset(request)
        
        # Skip isolation for superusers
        if request.user.is_superuser:
            return qs
        
        # Check if user has an associated organization through team membership
        # This query pattern should match your specific way of associating users with organizations
        try:
            from Apps.entity.models import TeamMember
            organizations = TeamMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
            if organizations:
                return qs.filter(organization_id__in=organizations)
            return qs.none()  # No organization access
        except ImportError:
            # If entity app is not available, try a direct approach
            if hasattr(request.user, 'organization_id') and request.user.organization_id:
                return qs.filter(organization_id=request.user.organization_id)
            return qs
    
    def save_model(self, request, obj, form, change):
        """
        Set the organization when saving if not already set and not a superuser.
        """
        if not change and not getattr(obj, 'organization_id', None):
            try:
                from Apps.entity.models import TeamMember
                # Try to get the user's organization from team membership
                team_member = TeamMember.objects.filter(user=request.user).first()
                if team_member:
                    obj.organization_id = team_member.organization_id
            except ImportError:
                # If entity app is not available, try a direct approach
                if hasattr(request.user, 'organization_id') and request.user.organization_id:
                    obj.organization_id = request.user.organization_id
        
        # Prevent changing organization if not a superuser
        if change and not request.user.is_superuser:
            # Get the original object
            original = self.model.objects.get(pk=obj.pk)
            if original.organization_id != obj.organization_id:
                raise PermissionDenied("You are not allowed to change the organization of this object.")
        
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """
        Check if user has permission to change the object based on organization.
        """
        if obj is None:
            return super().has_change_permission(request, obj)
        
        # Superusers can change anything
        if request.user.is_superuser:
            return True
        
        # Check if the object belongs to the user's organization
        try:
            from Apps.entity.models import TeamMember
            user_orgs = TeamMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
            return obj.organization_id in user_orgs
        except ImportError:
            # If entity app is not available, try a direct approach
            if hasattr(request.user, 'organization_id'):
                return obj.organization_id == request.user.organization_id
            return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Check if user has permission to delete the object based on organization.
        """
        # Reuse the same logic as for change permission
        return self.has_change_permission(request, obj)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter foreign key choices by organization for non-superusers.
        """
        if not request.user.is_superuser:
            # Check if the related model has organization field
            related_model = db_field.remote_field.model
            if hasattr(related_model, 'organization'):
                try:
                    from Apps.entity.models import TeamMember
                    user_orgs = TeamMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
                    kwargs["queryset"] = related_model.objects.filter(organization_id__in=user_orgs)
                except ImportError:
                    # If entity app is not available, try a direct approach
                    if hasattr(request.user, 'organization_id') and request.user.organization_id:
                        kwargs["queryset"] = related_model.objects.filter(organization_id=request.user.organization_id)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Filter many-to-many choices by organization for non-superusers.
        """
        if not request.user.is_superuser:
            # Check if the related model has organization field
            related_model = db_field.remote_field.model
            if hasattr(related_model, 'organization'):
                try:
                    from Apps.entity.models import TeamMember
                    user_orgs = TeamMember.objects.filter(user=request.user).values_list('organization_id', flat=True)
                    kwargs["queryset"] = related_model.objects.filter(organization_id__in=user_orgs)
                except ImportError:
                    # If entity app is not available, try a direct approach
                    if hasattr(request.user, 'organization_id') and request.user.organization_id:
                        kwargs["queryset"] = related_model.objects.filter(organization_id=request.user.organization_id)
        
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# Register your models here.
