from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, filters, decorators, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from .models import Project, Task, ProjectTemplate, TaskTemplate, ProjectSchedule, ProjectPhase, Milestone, ProjectDiscussion, DiscussionAttachment, DiscussionNotification
from .serializers import (
    ProjectSerializer, TaskSerializer,
    ProjectTemplateSerializer, TaskTemplateSerializer,
    ProjectScheduleSerializer, ProjectPhaseSerializer, MilestoneSerializer,
    ProjectDiscussionSerializer, DiscussionAttachmentSerializer, DiscussionNotificationSerializer
)
from Apps.core.permissions import IsOwnerOrReadOnly, IsOrganizationMember
import logging
from django.utils import timezone
from django.core.cache import cache
import json

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

class ProjectScheduleViewSet(viewsets.ModelViewSet):
    queryset = ProjectSchedule.objects.all()
    serializer_class = ProjectScheduleSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'project__title']
    ordering_fields = ['created_at', 'estimated_start_date', 'estimated_end_date', 'progress']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter schedules based on user's project access and permissions
        """
        user = self.request.user
        logger.info(f"Getting schedule queryset for user: {user}")
        
        if user.has_perm('project.view_all_schedules'):
            logger.info("User has view_all_schedules permission")
            return ProjectSchedule.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        logger.info(f"User organizations: {list(user_organizations)}")
        
        queryset = ProjectSchedule.objects.filter(
            Q(project__owner=user) | 
            Q(project__team_members=user) |
            Q(project__organization__in=user_organizations)
        ).distinct()
        logger.info(f"Filtered schedule queryset count: {queryset.count()}")
        
        return queryset

    def perform_create(self, serializer):
        logger.info("Performing schedule create")
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        logger.info("Performing schedule update")
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def set_baseline(self, request, pk=None):
        """Set this schedule as the baseline"""
        schedule = self.get_object()
        
        # Check if another baseline exists
        if ProjectSchedule.objects.filter(project=schedule.project, is_baseline=True).exists():
            # Remove existing baseline
            existing_baseline = ProjectSchedule.objects.get(project=schedule.project, is_baseline=True)
            existing_baseline.is_baseline = False
            existing_baseline.save()
        
        # Set this schedule as baseline
        schedule.is_baseline = True
        schedule.save()
        
        return Response(
            ProjectScheduleSerializer(schedule).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get schedule progress details"""
        schedule = self.get_object()
        
        # Update progress before returning
        schedule.update_progress()
        
        # Get phase progress data
        phases_data = []
        for phase in schedule.phases.all():
            phase.update_progress()
            phases_data.append({
                'id': phase.id,
                'name': phase.name,
                'progress': phase.progress,
                'start_date': phase.start_date,
                'end_date': phase.end_date,
                'order': phase.order
            })
        
        # Get milestone completion data
        milestones_data = []
        for milestone in schedule.milestones.all():
            milestones_data.append({
                'id': milestone.id,
                'name': milestone.name,
                'status': milestone.status,
                'due_date': milestone.due_date,
                'completion_date': milestone.completion_date
            })
        
        return Response({
            'schedule_id': schedule.id,
            'project_title': schedule.project.title,
            'overall_progress': schedule.progress,
            'estimated_start_date': schedule.estimated_start_date,
            'estimated_end_date': schedule.estimated_end_date,
            'phases': phases_data,
            'milestones': milestones_data
        })


class ProjectPhaseViewSet(viewsets.ModelViewSet):
    queryset = ProjectPhase.objects.all()
    serializer_class = ProjectPhaseSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'start_date', 'end_date', 'progress']
    ordering = ['order', 'start_date']

    def get_queryset(self):
        """
        Filter phases based on user's schedule access and permissions
        """
        user = self.request.user
        
        if user.has_perm('project.view_all_phases'):
            return ProjectPhase.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        
        queryset = ProjectPhase.objects.filter(
            Q(schedule__project__owner=user) | 
            Q(schedule__project__team_members=user) |
            Q(schedule__project__organization__in=user_organizations)
        ).distinct()
        
        # Additional filters
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Change the order of a phase"""
        phase = self.get_object()
        new_order = request.data.get('order')
        
        if new_order is None:
            return Response(
                {"detail": "New order value is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phase.order = new_order
        phase.save()
        
        # Reorder other phases if needed
        schedule_phases = ProjectPhase.objects.filter(schedule=phase.schedule).exclude(id=phase.id).order_by('order')
        current_order = 1
        for other_phase in schedule_phases:
            if current_order == new_order:
                current_order += 1
            other_phase.order = current_order
            other_phase.save()
            current_order += 1
        
        return Response(
            ProjectPhaseSerializer(phase).data,
            status=status.HTTP_200_OK
        )


class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['due_date', 'status']
    ordering = ['due_date']

    def get_queryset(self):
        """
        Filter milestones based on user's schedule access and permissions
        """
        user = self.request.user
        
        if user.has_perm('project.view_all_milestones'):
            return Milestone.objects.all()
        
        # Get organizations where user is a member of any team
        user_organizations = user.team_memberships.values_list(
            'team__department__organization', flat=True
        ).distinct()
        
        queryset = Milestone.objects.filter(
            Q(schedule__project__owner=user) | 
            Q(schedule__project__team_members=user) |
            Q(schedule__project__organization__in=user_organizations)
        ).distinct()
        
        # Additional filters
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
            
        phase_id = self.request.query_params.get('phase_id')
        if phase_id:
            queryset = queryset.filter(phase_id=phase_id)
            
        status_value = self.request.query_params.get('status')
        if status_value:
            queryset = queryset.filter(status=status_value)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        
        milestone.complete()
        
        return Response(
            MilestoneSerializer(milestone).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change milestone status"""
        milestone = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Milestone.Status.choices):
            return Response(
                {"detail": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        milestone.status = new_status
        if new_status == Milestone.Status.COMPLETED:
            milestone.completion_date = timezone.now()
        elif new_status != Milestone.Status.COMPLETED:
            milestone.completion_date = None
        
        milestone.save()
        
        # Update progress on related objects
        if milestone.phase:
            milestone.phase.update_progress()
        milestone.schedule.update_progress()
        
        return Response(
            MilestoneSerializer(milestone).data,
            status=status.HTTP_200_OK
        )

class IsProjectMember(permissions.BasePermission):
    """
    Custom permission to only allow project members or owner to access discussions.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Get the project ID from URL
        project_id = view.kwargs.get('project_pk')
        if not project_id:
            return False
            
        # Get the project
        try:
            project = Project.objects.get(pk=project_id)
            
            # Check if user is the owner or a team member
            return (request.user == project.owner or 
                   request.user in project.team_members.all())
        except Project.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # Get the project (either directly or through a relation)
        if hasattr(obj, 'project'):
            project = obj.project
        elif hasattr(obj, 'discussion') and hasattr(obj.discussion, 'project'):
            project = obj.discussion.project
        else:
            return False
            
        # Check if user is the owner or a team member
        return (request.user == project.owner or 
               request.user in project.team_members.all())


class ProjectDiscussionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for project discussions.
    """
    serializer_class = ProjectDiscussionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    pagination_class = None  # Disable pagination for this viewset
    
    def get_queryset(self):
        """
        Get the discussions for a specific project.
        Cache the results for better performance.
        """
        project_id = self.kwargs.get('project_pk')
        
        # Check if we should bypass cache
        refresh = self.request.query_params.get('refresh', 'false').lower() == 'true'
        
        # Generate cache key
        cache_key = f'project_discussions_{project_id}'
        
        # Try to get from cache if not refreshing
        if not refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                return ProjectDiscussion.objects.filter(pk__in=[d['id'] for d in json.loads(cached_data)])
        
        # Get from database
        queryset = ProjectDiscussion.objects.filter(
            project_id=project_id,
            is_active=True
        ).select_related('created_by', 'updated_by', 'project')
        
        # Update cache
        serializer = ProjectDiscussionSerializer(queryset, many=True)
        cache.set(cache_key, json.dumps(serializer.data), 3600)  # Cache for 1 hour
        
        return queryset
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context['project_pk'] = self.kwargs.get('project_pk')
        return context
    
    def perform_create(self, serializer):
        """Create a new discussion for a project."""
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)
        
        # Save the discussion with the project
        discussion = serializer.save(project=project)
        
        # Invalidate cache
        cache_key = f'project_discussions_{project_id}'
        cache.delete(cache_key)
        
        return discussion
    
    def perform_update(self, serializer):
        """Update an existing discussion."""
        # Get project ID from URL
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)
        
        # Save the updated discussion
        discussion = serializer.save()
        
        # Invalidate cache
        cache_key = f'project_discussions_{project_id}'
        cache.delete(cache_key)
        
        return discussion
    
    def perform_destroy(self, instance):
        """
        Perform a soft delete by marking the discussion as inactive.
        """
        instance.is_active = False
        instance.save()
        
        # Invalidate cache
        project_id = self.kwargs.get('project_pk')
        cache_key = f'project_discussions_{project_id}'
        cache.delete(cache_key)


class DiscussionAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for discussion attachments.
    """
    serializer_class = DiscussionAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    pagination_class = None  # Disable pagination for this viewset
    
    def get_queryset(self):
        """Get attachments for a specific discussion."""
        discussion_id = self.kwargs.get('discussion_pk')
        return DiscussionAttachment.objects.filter(discussion_id=discussion_id)
    
    def perform_create(self, serializer):
        """Create a new attachment for a discussion."""
        discussion_id = self.kwargs.get('discussion_pk')
        discussion = get_object_or_404(
            ProjectDiscussion, 
            pk=discussion_id,
            project_id=self.kwargs.get('project_pk')
        )
        
        # Save the attachment with the discussion
        attachment = serializer.save(
            discussion=discussion,
            created_by=self.request.user,
            updated_by=self.request.user
        )
        
        return attachment


class DiscussionNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for discussion notifications.
    """
    serializer_class = DiscussionNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for this viewset
    
    def get_queryset(self):
        """Get notifications for a specific discussion."""
        discussion_id = self.kwargs.get('discussion_pk')
        return DiscussionNotification.objects.filter(
            discussion_id=discussion_id,
            user=self.request.user
        )
    
    @decorators.action(detail=True, methods=['post'])
    def mark_read(self, request, *args, **kwargs):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'notification marked as read'})


class UserDiscussionNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user's discussion notifications across all projects.
    """
    serializer_class = DiscussionNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for this viewset
    
    def get_queryset(self):
        """Get all notifications for the current user."""
        return DiscussionNotification.objects.filter(
            user=self.request.user
        ).select_related('discussion', 'discussion__project')
    
    @decorators.action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        DiscussionNotification.mark_all_as_read(request.user)
        return Response({'status': 'all notifications marked as read'})


class ProjectTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks within a specific project.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'status', 'priority']
    ordering = ['due_date']
    
    def get_queryset(self):
        """
        Get all tasks for a specific project.
        """
        project_id = self.kwargs.get('project_pk')
        return Task.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        """
        Create a task for the specified project.
        """
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_id)
        
        serializer.save(
            project=project,
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, project_pk=None, pk=None):
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


class ProjectTeamViewSet(viewsets.ViewSet):
    """
    API endpoint for managing project team members.
    """
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    
    def list(self, request, project_pk=None):
        """
        List all team members for a project.
        """
        project = get_object_or_404(Project, pk=project_pk)
        
        # Check if user has permission to view team members
        if not (request.user == project.owner or request.user in project.team_members.all()):
            return Response(
                {"detail": _("You do not have permission to view team members")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get team members including the owner
        team_members = list(project.team_members.all())
        team_members.append(project.owner)
        
        # Serialize the team members
        from Apps.users.serializers import UserSerializer
        serializer = UserSerializer(team_members, many=True)
        
        return Response(serializer.data)
    
    def create(self, request, project_pk=None):
        """
        Add team members to a project.
        """
        project = get_object_or_404(Project, pk=project_pk)
        
        # Check if user has permission to add team members
        if not (request.user == project.owner or request.user.has_perm('project.manage_project_members')):
            return Response(
                {"detail": _("You do not have permission to add team members")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get user IDs from request
        user_ids = request.data.get('user_ids', [])
        
        if not user_ids:
            return Response(
                {"detail": _("No user IDs provided")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add team members
        project.team_members.add(*user_ids)
        
        return Response(
            {"detail": _("Team members added successfully")},
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, project_pk=None, pk=None):
        """
        Remove a team member from a project.
        """
        project = get_object_or_404(Project, pk=project_pk)
        
        # Check if user has permission to remove team members
        if not (request.user == project.owner or request.user.has_perm('project.manage_project_members')):
            return Response(
                {"detail": _("You do not have permission to remove team members")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove team member
        from Apps.users.models import User
        team_member = get_object_or_404(User, pk=pk)
        
        # Check if trying to remove the owner
        if team_member == project.owner:
            return Response(
                {"detail": _("Cannot remove project owner from team")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        project.team_members.remove(team_member)
        
        return Response(
            {"detail": _("Team member removed successfully")},
            status=status.HTTP_204_NO_CONTENT
        )
