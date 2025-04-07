from rest_framework import viewsets, status
from rest_framework.response import Response
from Apps.rbac.models import Role, Permission
from Apps.rbac.serializers import RoleSerializer, PermissionSerializer

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing roles
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_queryset(self):
        """
        Filter roles by organization
        """
        if not self.request.user.organization:
            return self.queryset.none()
        return self.queryset.filter(organization=self.request.user.organization)

class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def get_queryset(self):
        """
        Filter permissions by organization
        """
        if not self.request.user.organization:
            return self.queryset.none()
        return self.queryset.filter(organization=self.request.user.organization) 