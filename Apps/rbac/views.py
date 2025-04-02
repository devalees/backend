"""
Views for RBAC.
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.apps import apps
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    RoleSerializer, RBACPermissionSerializer, FieldPermissionSerializer,
    RolePermissionSerializer, UserRoleSerializer, FieldPermissionAvailableFieldsSerializer,
    RoleAssignPermissionsSerializer, UserRoleMyRolesSerializer, UserRoleMyFieldPermissionsSerializer
)
from .models import Role, RBACPermission, FieldPermission, RolePermission, UserRole

User = get_user_model()

def get_permission_models():
    """Get permission models to avoid circular imports."""
    RBACPermission = apps.get_model('rbac', 'RBACPermission')
    FieldPermission = apps.get_model('rbac', 'FieldPermission')
    return RBACPermission, FieldPermission

def get_role_models():
    """Get role models to avoid circular imports."""
    Role = apps.get_model('rbac', 'Role')
    RolePermission = apps.get_model('rbac', 'RolePermission')
    UserRole = apps.get_model('rbac', 'UserRole')
    return Role, RolePermission, UserRole

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(user_roles__user=self.request.user).distinct()

    def perform_create(self, serializer):
        """Create a new role."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update a role."""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Delete a role."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        instance.delete()

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        role = self.get_object()
        permission_ids = request.data.get('permissions', [])
        
        # Clear existing permissions
        RolePermission.objects.filter(role=role).delete()
        
        # Add new permissions
        permissions = RBACPermission.objects.filter(id__in=permission_ids)
        for permission in permissions:
            RolePermission.objects.create(
                role=role,
                permission=permission,
                created_by=request.user,
                updated_by=request.user
            )
        
        return Response(status=status.HTTP_200_OK)

class RBACPermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RBACPermission model.
    """
    queryset = RBACPermission.objects.all()
    serializer_class = RBACPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_superuser:
            return self.queryset.all()
        return self.queryset.filter(
            Q(created_by=self.request.user) |
            Q(role_permissions__role__user_roles__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        """Create a new permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update a permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Delete a permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        instance.delete()

class FieldPermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing field permissions.
    """
    queryset = FieldPermission.objects.all()
    serializer_class = FieldPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(
            Q(created_by=self.request.user) |
            Q(role_permissions__role__user_roles__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionDenied
        instance.delete()

    @action(detail=False, methods=['get'], url_path='available-fields')
    def available_fields(self, request):
        """
        Get available fields for field permissions.
        """
        if not request.user.is_superuser:
            raise PermissionDenied
            
        content_type_id = request.query_params.get('content_type')
        if not content_type_id:
            # Return all available content types with their fields
            content_types = ContentType.objects.all()
            result = []
            for ct in content_types:
                try:
                    model_class = ct.model_class()
                    if model_class:
                        fields = [
                            field.name for field in model_class._meta.get_fields()
                            if not field.is_relation or field.many_to_one
                        ]
                        result.append({
                            'id': ct.id,
                            'app_label': ct.app_label,
                            'model': ct.model,
                            'fields': fields
                        })
                except Exception:
                    continue
            return Response(result)

        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()
            if not model_class:
                return Response(
                    {'error': 'Model not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            fields = [
                field.name for field in model_class._meta.get_fields()
                if not field.is_relation or field.many_to_one
            ]
            return Response({
                'id': content_type.id,
                'app_label': content_type.app_label,
                'model': content_type.model,
                'fields': fields
            })
        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing role permissions.
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(
            Q(created_by=self.request.user) |
            Q(role__user_roles__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        """Create a new role permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """Update a role permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Delete a role permission."""
        if not self.request.user.is_superuser:
            raise PermissionDenied
        instance.delete()

    @action(detail=False, methods=['get'])
    def field_permissions(self, request):
        """Get field permissions for the current user's roles."""
        field_permissions = FieldPermission.objects.filter(
            role_permissions__role__user_roles__user=request.user
        ).distinct()
        serializer = FieldPermissionSerializer(field_permissions, many=True)
        return Response(serializer.data)

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user roles.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.filter(
            Q(user=self.request.user) |
            Q(created_by=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def my_roles(self, request):
        """Get roles assigned to the current user."""
        roles = Role.objects.filter(user_roles__user=request.user).distinct()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_field_permissions(self, request):
        """Get field permissions for the current user's roles."""
        field_permissions = FieldPermission.objects.filter(
            role_permissions__role__user_roles__user=request.user
        ).distinct()
        serializer = FieldPermissionSerializer(field_permissions, many=True)
        return Response(serializer.data)

class FieldPermissionAvailableFieldsViewSet(viewsets.ViewSet):
    """ViewSet for getting available fields for field permissions."""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Get available fields for field permissions."""
        if not request.user.is_superuser:
            raise PermissionDenied
        content_type_id = request.query_params.get('content_type_id')
        if not content_type_id:
            return Response({'error': 'content_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model = content_type.model_class()
            fields = [field.name for field in model._meta.get_fields()]
            return Response({'fields': fields})
        except ContentType.DoesNotExist:
            return Response({'error': 'Content type not found'}, status=status.HTTP_404_NOT_FOUND)

class RoleAssignPermissionsViewSet(viewsets.ViewSet):
    """ViewSet for assigning permissions to roles."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RoleAssignPermissionsSerializer

    def create(self, request, role_id=None):
        """Assign permissions to a role."""
        if not request.user.is_superuser:
            raise PermissionDenied

        Role, RolePermission, UserRole = get_role_models()
        RBACPermission, FieldPermission = get_permission_models()

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Clear existing permissions
        RolePermission.objects.filter(role=role).delete()

        # Assign new permissions
        for permission in serializer.validated_data['permissions']:
            RolePermission.objects.create(
                role=role,
                permission=permission,
                created_by=request.user
            )

        # Assign field permissions if provided
        if 'field_permissions' in serializer.validated_data:
            for field_permission in serializer.validated_data['field_permissions']:
                RolePermission.objects.create(
                    role=role,
                    field_permission=field_permission,
                    created_by=request.user
                )

        return Response({'message': 'Permissions assigned successfully'})

class UserRoleMyRolesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for getting user's roles."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserRoleMyRolesSerializer

    def get_queryset(self):
        """Get roles for the current user."""
        Role, RolePermission, UserRole = get_role_models()
        return UserRole.objects.filter(user=self.request.user)

class UserRoleMyFieldPermissionsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for getting user's field permissions."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserRoleMyFieldPermissionsSerializer

    def get_queryset(self):
        """Get field permissions for the current user."""
        Role, RolePermission, UserRole = get_role_models()
        return RolePermission.objects.filter(
            role__users__user=self.request.user,
            field_permission__isnull=False
        ).distinct() 