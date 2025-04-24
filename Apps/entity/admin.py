from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Organization, Department, Team, TeamMember

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'view_on_site')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    def view_on_site(self, obj):
        url = reverse('api:organization-detail', kwargs={'pk': obj.pk})
        return format_html('<a href="{}">View on site</a>', url)
    view_on_site.short_description = 'View on site'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'parent', 'is_active', 'view_on_site')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'description', 'organization__name')
    ordering = ('organization', 'name')
    raw_id_fields = ('parent',)

    def view_on_site(self, obj):
        url = reverse('api:department-detail', kwargs={'pk': obj.pk})
        return format_html('<a href="{}">View on site</a>', url)
    view_on_site.short_description = 'View on site'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'parent', 'is_active', 'view_on_site')
    list_filter = ('department', 'is_active')
    search_fields = ('name', 'description', 'department__name')
    ordering = ('department', 'name')
    raw_id_fields = ('parent',)

    def view_on_site(self, obj):
        url = reverse('api:team-detail', kwargs={'pk': obj.pk})
        return format_html('<a href="{}">View on site</a>', url)
    view_on_site.short_description = 'View on site'

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'is_active', 'view_on_site')
    list_filter = ('team', 'role', 'is_active')
    search_fields = ('user__username', 'team__name')
    ordering = ('team', 'user')
    raw_id_fields = ('user', 'team')

    def view_on_site(self, obj):
        url = reverse('api:team_members-detail', kwargs={'pk': obj.pk})
        return format_html('<a href="{}">View on site</a>', url)
    view_on_site.short_description = 'View on site'
