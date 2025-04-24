from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Role, Permission, UserRole, Resource, ResourceAccess, OrganizationContext, Audit
from ..serializers import RoleSerializer, PermissionSerializer, ResourceSerializer, ResourceAccessSerializer, ResourceAccessUpdateSerializer, OrganizationContextSerializer, AuditSerializer, UserRoleSerializer
from .pagination import RBACPagination
from .response_formatters import BaseResponseFormatter
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class UserTrackedViewSet(viewsets.ModelViewSet):
    """Base ViewSet that automatically sets created_by and updated_by fields"""
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )

class RoleViewSet(UserTrackedViewSet):
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

class PermissionViewSet(UserTrackedViewSet):
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

class ResourceViewSet(UserTrackedViewSet):
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
    
    def _extract_json_api_data(self, request_data):
        """Extract data from JSON:API format"""
        if not isinstance(request_data, dict) or 'data' not in request_data:
            return request_data
            
        data = request_data['data']
        if not isinstance(data, dict):
            return request_data
            
        result = {}
        
        # Extract attributes
        if 'attributes' in data:
            result.update(data['attributes'])
            
        # Extract relationships
        if 'relationships' in data:
            for field, value in data['relationships'].items():
                if isinstance(value, dict) and 'data' in value:
                    rel_data = value['data']
                    if isinstance(rel_data, dict) and 'id' in rel_data:
                        result[field] = rel_data['id']
                    elif isinstance(rel_data, list):
                        result[field] = [item['id'] for item in rel_data if isinstance(item, dict) and 'id' in item]
                        
        return result
    
    def create(self, request, *args, **kwargs):
        """Create resource with formatted response"""
        data = self._extract_json_api_data(request.data)
        serializer = self.get_serializer(data=data)
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
        data = self._extract_json_api_data(request.data)
        serializer = self.get_serializer(instance, data=data, partial=partial)
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

class ResourceAccessViewSet(UserTrackedViewSet):
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
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({'message': 'Resource access activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a resource access"""
        resource_access = self.get_object()
        resource_access.deactivate()
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({'message': 'Resource access deactivated'})

class OrganizationContextViewSet(UserTrackedViewSet):
    """ViewSet for OrganizationContext model"""
    
    queryset = OrganizationContext.objects.all()
    serializer_class = OrganizationContextSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter organization contexts by organization"""
        # Superusers can see all organization contexts
        if self.request.user.is_superuser:
            return OrganizationContext.objects.all()
        # Regular users can only see organization contexts from their organization
        return OrganizationContext.objects.filter(organization=self.request.user.organization)
    
    def list(self, request, *args, **kwargs):
        """List organization contexts with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve organization context with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    def _extract_json_api_data(self, request_data):
        """Extract data from JSON:API format"""
        if not isinstance(request_data, dict) or 'data' not in request_data:
            return request_data
            
        data = request_data['data']
        if not isinstance(data, dict):
            return request_data
            
        result = {}
        
        # Extract attributes
        if 'attributes' in data:
            result.update(data['attributes'])
            
        # Extract relationships
        if 'relationships' in data:
            for field, value in data['relationships'].items():
                if isinstance(value, dict) and 'data' in value:
                    if isinstance(value['data'], dict):
                        result[field] = value['data'].get('id')
                    elif isinstance(value['data'], list):
                        result[field] = [item.get('id') for item in value['data']]
                    else:
                        result[field] = None
                else:
                    result[field] = None
        
        return result
    
    def create(self, request, *args, **kwargs):
        """Create organization context with formatted response"""
        data = self._extract_json_api_data(request.data)
        serializer = self.get_serializer(data=data)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return formatter.format_detail_response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update organization context with formatted response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = self._extract_json_api_data(request.data)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return formatter.format_detail_response(serializer.data)
        except ValidationError as e:
            return formatter.format_error_response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete organization context with formatted response"""
        instance = self.get_object()
        self.perform_destroy(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an organization context"""
        context = self.get_object()
        context.activate()
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({'message': 'Organization context activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an organization context"""
        context = self.get_object()
        context.deactivate()
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({'message': 'Organization context deactivated'})
    
    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get ancestors of an organization context"""
        context = self.get_object()
        ancestors = context.get_ancestors()
        serializer = self.get_serializer(ancestors, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get descendants of an organization context"""
        context = self.get_object()
        descendants = context.get_descendants()
        serializer = self.get_serializer(descendants, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get direct children of an organization context"""
        context = self.get_object()
        children = context.get_all_children()
        serializer = self.get_serializer(children, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def parents(self, request, pk=None):
        """Get all parents of an organization context"""
        context = self.get_object()
        parents = context.get_all_parents()
        serializer = self.get_serializer(parents, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)

class AuditViewSet(UserTrackedViewSet):
    """ViewSet for Audit model"""
    
    queryset = Audit.objects.all()
    serializer_class = AuditSerializer
    pagination_class = RBACPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter audits by organization and apply filters"""
        queryset = Audit.objects.filter(organization=self.request.user.organization)
        
        # Apply filters
        resource_type = self.request.query_params.get('resource_type')
        action = self.request.query_params.get('action')
        user_id = self.request.query_params.get('user')
        status = self.request.query_params.get('status')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if action:
            queryset = queryset.filter(action=action)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if status:
            queryset = queryset.filter(status=status)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        return queryset.order_by('-timestamp')
    
    def list(self, request, *args, **kwargs):
        """List audits with formatted response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_list_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve audit with formatted response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """Generate compliance report"""
        report_type = request.query_params.get('report_type', 'comprehensive')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Validate report type
        valid_report_types = ['role_changes', 'permission_changes', 'user_role_assignments', 
                            'resource_access', 'comprehensive']
        if report_type not in valid_report_types:
            raise ValidationError(f"Invalid report type. Must be one of: {', '.join(valid_report_types)}")
        
        # Validate date range
        if start_date and end_date:
            try:
                start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
                if start > end:
                    raise ValidationError("Start date must be before end date")
            except ValueError:
                raise ValidationError("Invalid date format. Use YYYY-MM-DD")
        
        # Get base queryset
        queryset = self.get_queryset()
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Generate report based on type
        report_data = {}
        
        if report_type in ['role_changes', 'comprehensive']:
            report_data['role_changes'] = list(queryset.filter(
                action__in=['role_created', 'role_updated', 'role_deleted']
            ).values())
            
        if report_type in ['permission_changes', 'comprehensive']:
            report_data['permission_changes'] = list(queryset.filter(
                action__in=['permission_created', 'permission_updated', 'permission_deleted']
            ).values())
            
        if report_type in ['user_role_assignments', 'comprehensive']:
            report_data['user_role_assignments'] = list(queryset.filter(
                action__in=['user_role_assigned', 'user_role_removed']
            ).values())
            
        if report_type in ['resource_access', 'comprehensive']:
            report_data['resource_access'] = list(queryset.filter(
                action__in=['resource_accessed', 'resource_created', 'resource_updated', 'resource_deleted']
            ).values())
        
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({'attributes': report_data})
    
    @action(detail=False, methods=['post'])
    def cleanup_expired(self, request):
        """Clean up expired audit logs"""
        # Get current time
        now = timezone.now()
        
        # Find expired audits
        expired_audits = Audit.objects.filter(
            organization=request.user.organization,
            timestamp__lt=now - timezone.timedelta(days=Audit.DEFAULT_RETENTION_PERIOD)
        )
        
        # Count and delete expired audits
        deleted_count = expired_audits.count()
        expired_audits.delete()
        
        formatter = BaseResponseFormatter(request, serializer_class=self.serializer_class)
        return formatter.format_detail_response({
            'attributes': {
                'deleted_count': deleted_count
            }
        }) 