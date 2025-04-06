from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserRole
from .serializers import UserRoleSerializer, UserRoleUpdateSerializer
from .permissions import HasOrganizationPermission
from django.contrib.auth import get_user_model

# Create your views here.

class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user role assignments.
    Supports CRUD operations and role activation/deactivation.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, HasOrganizationPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'role', 'organization', 'is_active', 'is_delegated']

    def get_queryset(self):
        """Filter queryset based on user's organization"""
        return self.queryset.filter(organization=self.request.user.organization)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['update', 'partial_update']:
            return UserRoleUpdateSerializer
        return UserRoleSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user role assignment"""
        user_role = self.get_object()
        user_role.activate()
        return Response({'status': 'role activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user role assignment"""
        user_role = self.get_object()
        user_role.deactivate()
        return Response({'status': 'role deactivated'})

    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        """Delegate a role to another user"""
        user_role = self.get_object()
        target_user_id = request.data.get('user')
        
        if not target_user_id:
            return Response(
                {'error': 'Target user is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            User = get_user_model()
            target_user = User.objects.get(id=target_user_id)

            delegated_role = UserRole.objects.create(
                user=target_user,
                role=user_role.role,
                organization=user_role.organization,
                assigned_by=request.user,
                delegated_by=user_role,
                is_delegated=True
            )
            serializer = self.get_serializer(delegated_role)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Target user not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        """Set organization from request user"""
        serializer.save(organization=self.request.user.organization)
