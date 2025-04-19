from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from . import views
import logging

logger = logging.getLogger(__name__)

app_name = 'project'

# Debug logging
logger.info("Loading project URLs configuration")

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'project-templates', views.ProjectTemplateViewSet, basename='project-template')
router.register(r'task-templates', views.TaskTemplateViewSet, basename='task-template')
router.register(r'schedules', views.ProjectScheduleViewSet, basename='schedule')
router.register(r'phases', views.ProjectPhaseViewSet, basename='phase')
router.register(r'milestones', views.MilestoneViewSet, basename='milestone')
router.register(r'user-notifications', views.UserDiscussionNotificationViewSet, basename='user-discussion-notifications')
router.register(r'project-tasks', views.ProjectTaskViewSet, basename='project-task')

# Create nested routers
project_router = NestedDefaultRouter(router, r'projects', lookup='project')
project_router.register(r'tasks', views.ProjectTaskViewSet, basename='project-tasks')
project_router.register(r'team', views.ProjectTeamViewSet, basename='project-team')
project_router.register(r'discussions', views.ProjectDiscussionViewSet, basename='project-discussions')

# Create nested router for discussions
discussion_router = NestedDefaultRouter(project_router, r'discussions', lookup='discussion')
discussion_router.register(r'attachments', views.DiscussionAttachmentViewSet, basename='discussion-attachments')
discussion_router.register(r'notifications', views.DiscussionNotificationViewSet, basename='discussion-notifications')

# Custom URLs for time entries - these are needed for the time_entries actions
task_time_entries = [
    path('tasks/<int:pk>/time_entries/', views.TaskViewSet.as_view({'get': 'time_entries'}), name='task-time-entries'),
]

phase_time_entries = [
    path('phases/<int:pk>/time_entries/', views.ProjectPhaseViewSet.as_view({'get': 'time_entries'}), name='phase-time-entries'),
]

milestone_time_entries = [
    path('milestones/<int:pk>/time_entries/', views.MilestoneViewSet.as_view({'get': 'time_entries'}), name='milestone-time-entries'),
]

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    path('', include(discussion_router.urls)),
] + task_time_entries + phase_time_entries + milestone_time_entries

# Debug logging for URLs
for pattern in urlpatterns:
    if hasattr(pattern, 'name') and pattern.name:
        logger.debug(f"URL Pattern: {pattern.pattern} -> {pattern.name}")
    else:
        logger.debug(f"URL Pattern: {pattern.pattern} -> [no name]")

logger.debug("Project URLs loaded") 