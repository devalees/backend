from rest_framework.routers import DefaultRouter
from django.urls import path, include

# Import ViewSets from different apps
from Apps.users.views import UserViewSet
from Apps.project.views import (
    ProjectViewSet, TaskViewSet, ProjectTemplateViewSet, 
    TaskTemplateViewSet, ProjectScheduleViewSet, ProjectPhaseViewSet, 
    MilestoneViewSet, UserDiscussionNotificationViewSet, ProjectTaskViewSet
)
from Apps.rbac.views import UserRoleViewSet
from Apps.rbac.api.views import (
    RoleViewSet, PermissionViewSet, ResourceViewSet, 
    ResourceAccessViewSet, OrganizationContextViewSet, AuditViewSet
)
from Apps.documents.views import (
    DocumentViewSet, DocumentVersionViewSet, 
    DocumentClassificationViewSet, DocumentTagViewSet
)

# Create a central router
api_router = DefaultRouter()

# Register users app ViewSets
api_router.register(r'users', UserViewSet, basename='user')

# Register project app ViewSets
api_router.register(r'projects', ProjectViewSet, basename='project')
api_router.register(r'tasks', TaskViewSet, basename='task')
api_router.register(r'project-templates', ProjectTemplateViewSet, basename='project-template')
api_router.register(r'task-templates', TaskTemplateViewSet, basename='task-template')
api_router.register(r'schedules', ProjectScheduleViewSet, basename='schedule')
api_router.register(r'phases', ProjectPhaseViewSet, basename='phase')
api_router.register(r'milestones', MilestoneViewSet, basename='milestone')
api_router.register(r'user-notifications', UserDiscussionNotificationViewSet, basename='user-discussion-notifications')
api_router.register(r'project-tasks', ProjectTaskViewSet, basename='project-task')

# Register rbac app ViewSets
api_router.register(r'user-roles', UserRoleViewSet, basename='userrole')
api_router.register(r'roles', RoleViewSet, basename='role')
api_router.register(r'permissions', PermissionViewSet, basename='permission')
api_router.register(r'resources', ResourceViewSet, basename='resource')
api_router.register(r'resource-accesses', ResourceAccessViewSet, basename='resourceaccess')
api_router.register(r'organization-contexts', OrganizationContextViewSet, basename='organizationcontext')
api_router.register(r'audits', AuditViewSet, basename='audit')

# Register documents app ViewSets
api_router.register(r'documents', DocumentViewSet, basename='document')
api_router.register(r'versions', DocumentVersionViewSet, basename='document-version')
api_router.register(r'classifications', DocumentClassificationViewSet, basename='document-classification')
api_router.register(r'tags', DocumentTagViewSet, basename='document-tag')

# URL patterns for the API router
urlpatterns = [
    path('', include(api_router.urls)),
] 