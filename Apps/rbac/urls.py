from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PermissionViewSet,
    FieldPermissionViewSet,
    RoleViewSet,
    RolePermissionViewSet,
    UserRoleViewSet,
)

router = DefaultRouter()
router.register(r'permissions', PermissionViewSet)
router.register(r'field-permissions', FieldPermissionViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'role-permissions', RolePermissionViewSet)
router.register(r'user-roles', UserRoleViewSet)

app_name = 'rbac'

urlpatterns = [
    path('', include(router.urls)),
] 