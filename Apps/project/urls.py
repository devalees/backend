from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, TaskViewSet,
    ProjectTemplateViewSet, TaskTemplateViewSet
)
import logging

logger = logging.getLogger(__name__)

app_name = 'project'

# Debug logging
logger.info("Loading project URLs configuration")

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'project-templates', ProjectTemplateViewSet, basename='project-template')
router.register(r'task-templates', TaskTemplateViewSet, basename='task-template')

# The API URLs are now determined automatically by the router
urlpatterns = router.urls

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