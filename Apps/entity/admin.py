from django.contrib import admin
from .models import Organization, Department, Team, TeamMember

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'parent', 'is_active')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'description', 'organization__name')
    ordering = ('organization', 'name')
    raw_id_fields = ('parent',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'parent', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'description', 'department__name')
    ordering = ('department', 'name')
    raw_id_fields = ('parent',)

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'is_active')
    list_filter = ('team', 'role', 'is_active')
    search_fields = ('user__username', 'team__name')
    ordering = ('team', 'user')
    raw_id_fields = ('user', 'team')
