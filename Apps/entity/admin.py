from django.contrib import admin
from .models import Organization, Department, Team, TeamMember

class BaseModelAdmin(admin.ModelAdmin):
    """
    Base admin class with common functionality
    """
    pass

@admin.register(Organization)
class OrganizationAdmin(BaseModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Department)
class DepartmentAdmin(BaseModelAdmin):
    list_display = ('name', 'organization', 'description', 'created_at', 'updated_at')
    list_filter = ('organization', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'organization__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Team)
class TeamAdmin(BaseModelAdmin):
    list_display = ('name', 'department', 'description', 'created_at', 'updated_at')
    list_filter = ('department', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'department__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TeamMember)
class TeamMemberAdmin(BaseModelAdmin):
    list_display = ('team', 'user', 'role', 'created_at', 'updated_at')
    list_filter = ('team', 'role', 'created_at', 'updated_at')
    search_fields = ('team__name', 'user__username', 'role')
    readonly_fields = ('created_at', 'updated_at')
