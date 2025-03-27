from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseForbidden
from Apps.organizations.models import TeamMember

class OrganizationMiddleware:
    """Middleware to attach organization, department, and team to request"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip if user is not authenticated
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            return self.get_response(request)

        # Get user's most recent active team membership
        team_member = (
            TeamMember.objects
            .filter(
                user=request.user,
                is_active=True,
                team__is_active=True,
                team__department__is_active=True,
                team__department__organization__is_active=True
            )
            .order_by('-created_at')
            .first()
        )

        # Attach organization, department, and team to request if team membership exists
        if team_member:
            request.organization = team_member.team.department.organization
            request.department = team_member.team.department
            request.team = team_member.team
        else:
            request.organization = None

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required")

        if not hasattr(view_func, 'organization_required'):
            return None

        if not request.organization:
            return HttpResponseForbidden("Organization membership required")

        return None 