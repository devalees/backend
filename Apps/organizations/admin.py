from django.contrib import admin
from .models import Organization, Department, Team, TeamMember

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'description', 'organization__name', 'parent__name')
    ordering = ('organization', 'name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'organization', 'description', 'is_active')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': 'Select a parent department to create a hierarchy. Maximum depth is 2 levels.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'is_active', 'created_at')
    list_filter = ('is_active', 'department__organization', 'department')
    search_fields = ('name', 'description', 'department__name', 'department__organization__name')
    ordering = ('department__organization', 'department', 'name')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'is_active', 'created_at')
    list_filter = ('is_active', 'team__department__organization', 'team__department', 'team')
    search_fields = ('user__username', 'user__email', 'team__name', 'role')
    ordering = ('-created_at',)
    autocomplete_fields = ['user']
