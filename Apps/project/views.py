from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Project, Task, ProjectTemplate, TaskTemplate
from .serializers import (
    ProjectSerializer, TaskSerializer,
    ProjectTemplateSerializer, TaskTemplateSerializer
)
from Apps.core.permissions import IsOwnerOrReadOnly, IsOrganizationMember
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter projects based on user's organization and permissions
        """
        user = self.request.user
        logger.info(f"Getting queryset for user: {user}")
        
        if user.has_perm('project.view_all_projects'):
            logger.info("User has view_all_projects permission")
            return Project.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        logger.info(f"User organizations: {list(user_organizations)}")
        
        queryset = Project.objects.filter(
            Q(owner=user) | 
            Q(team_members=user) |
            Q(organization__in=user_organizations)
        ).distinct()
        logger.info(f"Filtered queryset count: {queryset.count()}")
        
        return queryset

    def list(self, request, *args, **kwargs):
        logger.info("ProjectViewSet.list called")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request user: {request.user}")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info("ProjectViewSet.create called")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request user: {request.user}")
        logger.info(f"Request data: {request.data}")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        logger.info("Performing create")
        serializer.save(
            owner=self.request.user,
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        logger.info("Performing update")
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def add_team_members(self, request, pk=None):
        """Add team members to the project"""
        project = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {"detail": _("No user IDs provided")},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.team_members.add(*user_ids)
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def remove_team_members(self, request, pk=None):
        """Remove team members from the project"""
        project = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {"detail": _("No user IDs provided")},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.team_members.remove(*user_ids)
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_200_OK
        )

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'status', 'priority']
    ordering = ['due_date']

    def get_queryset(self):
        """
        Filter tasks based on user's projects and permissions
        """
        user = self.request.user
        logger.info(f"Getting task queryset for user: {user}")
        
        if user.has_perm('project.view_all_tasks'):
            logger.info("User has view_all_tasks permission")
            return Task.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        logger.info(f"User organizations: {list(user_organizations)}")
        
        queryset = Task.objects.filter(
            Q(project__owner=user) |
            Q(project__team_members=user) |
            Q(assigned_to=user) |
            Q(project__organization__in=user_organizations)
        ).distinct()
        logger.info(f"Filtered task queryset count: {queryset.count()}")
        
        return queryset

    def perform_create(self, serializer):
        logger.info("Performing task create")
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        logger.info("Performing task update")
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a user"""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": _("No user ID provided")},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.assigned_to_id = user_id
        task.save()
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change task status"""
        task = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value or status_value not in dict(Task.Status.choices):
            return Response(
                {"detail": _("Invalid status value")},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.status = status_value
        task.save()
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )

class ProjectTemplateViewSet(viewsets.ModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'estimated_duration']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter templates based on user's organization and permissions
        """
        user = self.request.user
        logger.info(f"Getting template queryset for user: {user}")
        
        if user.has_perm('project.view_all_project_templates'):
            logger.info("User has view_all_project_templates permission")
            return ProjectTemplate.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        logger.info(f"User organizations: {list(user_organizations)}")
        
        queryset = ProjectTemplate.objects.filter(
            organization__in=user_organizations
        ).distinct()
        logger.info(f"Filtered template queryset count: {queryset.count()}")
        
        return queryset

    def perform_create(self, serializer):
        logger.info("Creating project template")
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        logger.info("Updating project template")
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def create_project(self, request, pk=None):
        """Create a new project from this template"""
        template = self.get_object()
        serializer = ProjectTemplateSerializer(template, context={'request': request})
        
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        owner_id = request.data.get('owner_id')
        
        if not start_date or not end_date:
            return Response(
                {"detail": _("Start date and end date are required")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        owner = None
        if owner_id:
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": _("Owner not found")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        project = serializer.create_project(start_date, end_date, owner)
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED
        )

class TaskTemplateViewSet(viewsets.ModelViewSet):
    queryset = TaskTemplate.objects.all()
    serializer_class = TaskTemplateSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['order', 'created_at', 'estimated_duration']
    ordering = ['order', 'created_at']

    def get_queryset(self):
        """
        Filter task templates based on user's organization and permissions
        """
        user = self.request.user
        logger.info(f"Getting task template queryset for user: {user}")
        
        if user.has_perm('project.view_all_task_templates'):
            logger.info("User has view_all_task_templates permission")
            return TaskTemplate.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        logger.info(f"User organizations: {list(user_organizations)}")
        
        queryset = TaskTemplate.objects.filter(
            project_template__organization__in=user_organizations
        ).distinct()
        logger.info(f"Filtered task template queryset count: {queryset.count()}")
        
        return queryset

    def perform_create(self, serializer):
        logger.info("Creating task template")
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        logger.info("Updating task template")
        serializer.save(updated_by=self.request.user)
