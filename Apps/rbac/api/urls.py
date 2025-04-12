from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RoleViewSet, PermissionViewSet,
    OrganizationViewSet, AuditViewSet, ResourceViewSet, ResourceAccessViewSet
)

# Remove the app_name here since it's causing namespace conflicts
# app_name = 'rbac'  # Add app_name for namespace

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'resource-accesses', ResourceAccessViewSet, basename='resourceaccess')
router.register(r'audits', AuditViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
] 