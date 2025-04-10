from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Role, Permission, UserRole
from ..serializers import RoleSerializer, PermissionSerializer
from .pagination import RBACPagination
from .response_formatters import BaseResponseFormatter

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