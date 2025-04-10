from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Role, Permission, UserRole, Resource, ResourceAccess
from ..serializers import RoleSerializer, PermissionSerializer, ResourceSerializer, ResourceAccessSerializer, ResourceAccessUpdateSerializer
from .pagination import RBACPagination
from .response_formatters import BaseResponseFormatter
from django.contrib.auth import get_user_model

User = get_user_model()

class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for Role model"""
    
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter roles by organization"""
        return Role.objects.filter(organization=self.request.user.organization)
    
    def list(self, request, *args, **kwargs):
        """List roles with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve role with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create role with formatted response"""
        serializer = self.get_serializer(data=request.data)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return formatter.format_detail_response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update role with formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return formatter.format_detail_response(serializer.data)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete role with formatted response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Get role permissions with formatted response"""
        role = self.get_object()
        permissions = role.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=PermissionSerializer)
        return formatter.format_list_response(serializer.data)

class PermissionViewSet(viewsets.ModelViewSet):
    """ViewSet for Permission model"""
    
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter permissions by organization"""
        return Permission.objects.filter(organization=self.request.user.organization)
    
    def list(self, request, *args, **kwargs):
        """List permissions with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve permission with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create permission with formatted response"""
        serializer = self.get_serializer(data=request.data)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return formatter.format_detail_response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update permission with formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return formatter.format_detail_response(serializer.data)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete permission with formatted response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({}, status=status.HTTP_204_NO_CONTENT)

class ResourceViewSet(viewsets.ModelViewSet):
    """ViewSet for Resource model"""
    
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter resources by organization"""
        return Resource.objects.filter(organization=self.request.user.organization)
    
    def list(self, request, *args, **kwargs):
        """List resources with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve resource with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create resource with formatted response"""
        serializer = self.get_serializer(data=request.data)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return formatter.format_detail_response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update resource with formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return formatter.format_detail_response(serializer.data)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete resource with formatted response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def grant_access(self, request, pk=None):
        """Grant access to a resource"""
        resource = self.get_object()
        user_id = request.data.get('user')
        access_type = request.data.get('access_type')
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        
        if not user_id or not access_type:
            return formatter.format_error_response(
                "User and access type are required",
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate access type
        valid_access_types = ['read', 'write', 'admin']
        if access_type not in valid_access_types:
            return formatter.format_error_response(
                f"Invalid access type. Must be one of: {', '.join(valid_access_types)}",
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            # Check if access already exists
            if resource.has_access(user, access_type):
                return formatter.format_error_response(
                    f"User {user.username} already has {access_type} access to this resource",
                    status=status.HTTP_400_BAD_REQUEST
                )
            resource.grant_access(user, access_type)
            return formatter.format_detail_response(
                {"message": f"Access granted to user {user.username}"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return formatter.format_error_response(
                "User not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return formatter.format_error_response(
                str(e),
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def revoke_access(self, request, pk=None):
        """Revoke access from a resource"""
        resource = self.get_object()
        user_id = request.data.get('user')
        access_type = request.data.get('access_type')
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        
        if not user_id:
            return formatter.format_error_response(
                "User is required",
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate access type if provided
        if access_type:
            valid_access_types = ['read', 'write', 'admin']
            if access_type not in valid_access_types:
                return formatter.format_error_response(
                    f"Invalid access type. Must be one of: {', '.join(valid_access_types)}",
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            user = User.objects.get(id=user_id)
            # Check if access exists before revoking
            if access_type and not resource.has_access(user, access_type):
                return formatter.format_error_response(
                    f"User {user.username} does not have {access_type} access to this resource",
                    status=status.HTTP_400_BAD_REQUEST
                )
            resource.revoke_access(user, access_type)
            return formatter.format_detail_response(
                {"message": f"Access revoked from user {user.username}"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return formatter.format_error_response(
                "User not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return formatter.format_error_response(
                str(e),
                status=status.HTTP_400_BAD_REQUEST
            )

class ResourceAccessViewSet(viewsets.ModelViewSet):
    """ViewSet for ResourceAccess model"""
    
    queryset = ResourceAccess.objects.all()
    serializer_class = ResourceAccessSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter resource access by organization"""
        return ResourceAccess.objects.filter(organization=self.request.user.organization)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['update', 'partial_update']:
            return ResourceAccessUpdateSerializer
        return ResourceAccessSerializer
    
    def list(self, request, *args, **kwargs):
        """List resource access with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve resource access with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create resource access with formatted response"""
        serializer = self.get_serializer(data=request.data)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return formatter.format_detail_response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update resource access with formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return formatter.format_detail_response(serializer.data)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete resource access with formatted response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a resource access"""
        resource_access = self.get_object()
        resource_access.activate()
        resource_access.save()
        
        serializer = self.get_serializer(resource_access)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a resource access"""
        resource_access = self.get_object()
        resource_access.deactivate()
        resource_access.save()
        
        serializer = self.get_serializer(resource_access)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data) 