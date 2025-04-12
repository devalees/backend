from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRoleViewSet
from .api.views import RoleViewSet, PermissionViewSet, ResourceViewSet, ResourceAccessViewSet, OrganizationContextViewSet, AuditViewSet

app_name = 'rbac'  # Add app_name for namespace

router = DefaultRouter()
router.register(r'user-roles', UserRoleViewSet, basename='userrole')
router.register(r'audits', AuditViewSet, basename='audit')

# Include the API URLs directly in the urlpatterns
api_router = DefaultRouter()
api_router.register(r'roles', RoleViewSet, basename='role')
api_router.register(r'permissions', PermissionViewSet, basename='permission')
api_router.register(r'resources', ResourceViewSet, basename='resource')
api_router.register(r'resource-accesses', ResourceAccessViewSet, basename='resourceaccess')
api_router.register(r'organization-contexts', OrganizationContextViewSet, basename='organizationcontext')

urlpatterns = [
    path('', include(router.urls)),
    path('api/', include(api_router.urls)),
] 