"""
URLs for RBAC.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet,
    RBACPermissionViewSet,
    FieldPermissionViewSet,
    RolePermissionViewSet,
    UserRoleViewSet,
    FieldPermissionAvailableFieldsViewSet,
)

app_name = 'rbac'

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', RBACPermissionViewSet, basename='permission')
router.register(r'field-permissions', FieldPermissionViewSet, basename='fieldpermission')
router.register(r'role-permissions', RolePermissionViewSet, basename='rolepermission')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

urlpatterns = [
    path('', include(router.urls)),
    path('field-permissions/available-fields/', 
         FieldPermissionAvailableFieldsViewSet.as_view({'get': 'list'}), 
         name='available-fields'),
] 