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

# Create nested routers
project_router = NestedDefaultRouter(router, r'projects', lookup='project')
project_router.register(r'tasks', views.ProjectTaskViewSet, basename='project-tasks')
project_router.register(r'team', views.ProjectTeamViewSet, basename='project-team')
project_router.register(r'discussions', views.ProjectDiscussionViewSet, basename='project-discussions')

# Create nested router for discussions
discussion_router = NestedDefaultRouter(project_router, r'discussions', lookup='discussion')
discussion_router.register(r'attachments', views.DiscussionAttachmentViewSet, basename='discussion-attachments')
discussion_router.register(r'notifications', views.DiscussionNotificationViewSet, basename='discussion-notifications')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    path('', include(discussion_router.urls)),
]

# Debug logging
logger.info("Project URLs registered:")
for pattern in urlpatterns:
    logger.info(f"Pattern: {pattern.pattern}")
    if hasattr(pattern, 'name'):
        logger.info(f"Name: {pattern.name}")
    if hasattr(pattern, 'view_class'):
        logger.info(f"View class: {pattern.view_class.__name__}")
    if hasattr(pattern, 'view_initkwargs'):
        logger.info(f"View initkwargs: {pattern.view_initkwargs}")
    if hasattr(pattern, 'callback'):
        logger.info(f"Callback: {pattern.callback}")
        if hasattr(pattern.callback, 'actions'):
            logger.info(f"Actions: {pattern.callback.actions}")

logger.debug("Project URLs loaded") 