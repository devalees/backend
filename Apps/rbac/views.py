import logging
from django.shortcuts import render
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from .models import Role, Permission, RolePermission, UserRole, FieldPermission
from .serializers import (
    RoleSerializer,
    PermissionSerializer,
    RolePermissionSerializer,
    UserRoleSerializer,
    FieldPermissionSerializer
)
from .permissions import IsAdminOrReadOnly, CanManageRoles
from rest_framework import status

logger = logging.getLogger(__name__)

class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing permissions.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['codename', 'content_type']
    search_fields = ['name', 'codename']
    ordering_fields = ['name', 'codename', 'created_at']
    ordering = ['codename']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        logger.debug("=== PermissionViewSet.create() Debug Log ===")
        logger.debug(f"Request data: {request.data}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request content type: {request.content_type}")
        logger.debug(f"Request user: {request.user}")
        logger.debug(f"Request user is_staff: {request.user.is_staff}")
        logger.debug(f"Request user is_superuser: {request.user.is_superuser}")
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request META: {request.META}")
        logger.debug(f"Request path: {request.path}")
        logger.debug(f"Request path_info: {request.path_info}")
        logger.debug(f"Request resolved: {request.resolver_match}")
        logger.debug(f"Request user permissions: {request.user.get_all_permissions()}")
        logger.debug(f"Request user groups: {request.user.groups.all()}")
        logger.debug("=== End Debug Log ===")
        return super().create(request, *args, **kwargs)

class FieldPermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing field permissions.
    """
    queryset = FieldPermission.objects.all()
    serializer_class = FieldPermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['content_type', 'field_name', 'permission_type']
    search_fields = ['field_name', 'description']
    ordering_fields = ['field_name', 'created_at']
    ordering = ['field_name']

    @action(detail=False, methods=['get'])
    def available_fields(self, request):
        """
        Get available fields for a specific content type.
        """
        content_type_id = request.query_params.get('content_type_id')
        if not content_type_id:
            return Response(
                {'error': 'content_type_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model = content_type.model_class()
            if not model:
                return Response(
                    {'error': 'Invalid content type: unable to get model class'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            fields = []
            for field in model._meta.get_fields():
                if field.name not in ['id', 'created_at', 'updated_at']:
                    fields.append({
                        'name': field.name,
                        'type': field.get_internal_type(),
                        'verbose_name': getattr(field, 'verbose_name', field.name)
                    })
            return Response(fields)
        except ContentType.DoesNotExist:
            return Response(
                {'error': 'Invalid content type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AttributeError:
            return Response(
                {'error': 'Invalid content type: model class not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageRoles]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """
        Assign permissions to a role.
        """
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        field_permission_ids = request.data.get('field_permission_ids', [])
        
        # Remove existing permissions
        role.role_permissions.all().delete()
        
        # Add new permissions
        for permission_id in permission_ids:
            try:
                permission = Permission.objects.get(id=permission_id)
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    created_by=request.user
                )
            except Permission.DoesNotExist:
                continue
        
        # Add new field permissions
        for field_permission_id in field_permission_ids:
            try:
                field_permission = FieldPermission.objects.get(id=field_permission_id)
                permission = Permission.objects.get(codename=field_permission.permission_type)
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    field_permission=field_permission,
                    created_by=request.user
                )
            except (FieldPermission.DoesNotExist, Permission.DoesNotExist):
                continue
        
        serializer = self.get_serializer(role)
        return Response(serializer.data)

class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing role permissions.
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageRoles]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'permission', 'field_permission']
    search_fields = ['role__name', 'permission__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user roles.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageRoles]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'role']
    search_fields = ['user__username', 'role__name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_roles(self, request):
        """
        Get roles assigned to the current user.
        """
        user_roles = UserRole.objects.filter(user=request.user)
        serializer = self.get_serializer(user_roles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_field_permissions(self, request):
        """
        Get field permissions assigned to the current user through roles.
        """
        user_roles = UserRole.objects.filter(user=request.user)
        field_permissions = set()
        for user_role in user_roles:
            role_permissions = user_role.role.role_permissions.filter(field_permission__isnull=False)
            for role_permission in role_permissions:
                field_permissions.add(role_permission.field_permission)
        
        serializer = FieldPermissionSerializer(list(field_permissions), many=True)
        return Response(serializer.data)
