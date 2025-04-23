from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone
from Apps.entity.models import Organization, TeamMember
from Apps.rbac.models import OrganizationContext

class OrganizationIsolationMiddleware:
    """
    Middleware to enforce organization isolation in the RBAC system.
    This middleware ensures that users can only access data from organizations they belong to.
    Superusers bypass this restriction and can access all organizations' data.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process the view before it's executed.
        This method is called before the view is executed and can be used to enforce organization isolation.
        """
        # Skip for admin views
        if request.path.startswith('/admin/'):
            return None
        
        # Skip for authentication views
        if request.path.startswith('/auth/'):
            return None
        
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for superusers - they can access all organizations
        if request.user.is_superuser:
            return None
        
        # Get the organization from the request
        organization_id = request.GET.get('organization_id')
        if not organization_id:
            return None
        
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return None
        
        # Check if the user belongs to the organization
        if not TeamMember.objects.filter(
            team__department__organization=organization,
            user=request.user,
            is_active=True
        ).exists():
            raise PermissionDenied("You don't have access to this organization")
        
        return None
    
    def process_template_response(self, request, response):
        """
        Process the template response.
        This method is called after the view is executed and can be used to add organization context to the response.
        """
        return response 