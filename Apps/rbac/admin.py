"""
Admin interface for RBAC.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.apps import apps
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from .models import Role, RolePermission, UserRole, RBACPermission, FieldPermission

User = get_user_model()

# Custom ContentType admin with search fields
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ['app_label', 'model']
    list_display = ['app_label', 'model']

# Register ContentType with custom admin
admin.site.register(ContentType, ContentTypeAdmin)

class RolePermissionInline(admin.TabularInline):
    """Inline admin for RolePermission model."""
    model = RolePermission
    extra = 1
    fields = ('permission', 'field_permission')
    autocomplete_fields = ['permission', 'field_permission']

@admin.register(RBACPermission)
class RBACPermissionAdmin(admin.ModelAdmin):
    """Admin interface for RBACPermission model."""
    list_display = ('content_type', 'codename', 'name')
    list_filter = ('content_type',)
    search_fields = ('codename', 'name', 'description')

@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    """Admin interface for FieldPermission model."""
    list_display = ('content_type', 'field_name', 'permission_type')
    list_filter = ('content_type', 'permission_type')
    search_fields = ('field_name', 'description')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    inlines = [RolePermissionInline]

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Admin interface for RolePermission model."""
    list_display = ('role', 'permission', 'field_permission')
    list_filter = ('role',)
    search_fields = ('role__name', 'permission__codename', 'field_permission__field_name')
    autocomplete_fields = ['permission', 'field_permission']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for UserRole model."""
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'role__name')

# Register admin classes when Django is ready
admin.autodiscover()
