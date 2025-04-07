from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from ..models import Role, Permission
from ..serializers import RoleSerializer, PermissionSerializer
from .utils import create_success_response, create_error_response
from .pagination import StandardResultsSetPagination

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get roles for the user's organization."""
        if not self.request.user.organization:
            return Role.objects.none()
        return Role.objects.filter(organization=self.request.user.organization)

    def create(self, request, *args, **kwargs):
        """Create a new role."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return create_success_response(
                data=serializer.data,
                message="Role created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return create_error_response(
            message="Failed to create role",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        """Update an existing role."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            self.perform_update(serializer)
            return create_success_response(
                data=serializer.data,
                message="Role updated successfully"
            )
        return create_error_response(
            message="Failed to update role",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a role."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return create_success_response(
            message="Role deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing permissions.
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get permissions for the user's organization."""
        if not self.request.user.organization:
            return Permission.objects.none()
        return Permission.objects.filter(organization=self.request.user.organization)

    def create(self, request, *args, **kwargs):
        """Create a new permission."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return create_success_response(
                data=serializer.data,
                message="Permission created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return create_error_response(
            message="Failed to create permission",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        """Update an existing permission."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        if serializer.is_valid():
            self.perform_update(serializer)
            return create_success_response(
                data=serializer.data,
                message="Permission updated successfully"
            )
        return create_error_response(
            message="Failed to update permission",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a permission."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return create_success_response(
            message="Permission deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        ) 