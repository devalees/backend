from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from .models import Role, Permission, FieldPermission, RolePermission, UserRole

# Custom ContentType admin with search fields
class ContentTypeAdmin(admin.ModelAdmin):
    search_fields = ['app_label', 'model']
    list_display = ['app_label', 'model']

# Register ContentType with custom admin
admin.site.register(ContentType, ContentTypeAdmin)

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    fields = ('permission', 'field_permission')
    autocomplete_fields = ['permission', 'field_permission']

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'codename', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'codename', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )

@admin.register(FieldPermission)
class FieldPermissionAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'field_name', 'permission_type', 'created_at')
    list_filter = ('content_type', 'permission_type', 'created_at')
    search_fields = ('field_name', 'content_type__model')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ['content_type']
    fieldsets = (
        (None, {
            'fields': ('content_type', 'field_name', 'permission_type')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RolePermissionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'field_permission', 'created_at')
    list_filter = ('role', 'permission', 'field_permission', 'created_at')
    search_fields = ('role__name', 'permission__name', 'field_permission__field_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ['role', 'permission', 'field_permission']
    fieldsets = (
        (None, {
            'fields': ('role', 'permission', 'field_permission')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'role__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ['user', 'role']
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        })
    )
