from django.contrib import admin
from .models import Project, Task, ProjectTemplate, TaskTemplate, ProjectSchedule, ProjectPhase, Milestone

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'owner', 'organization', 'start_date', 'end_date')
    list_filter = ('status', 'priority', 'organization')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'project', 'assigned_to', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'default_status', 'default_priority', 'estimated_duration')
    list_filter = ('default_status', 'default_priority', 'organization')
    search_fields = ('title', 'description')

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_template', 'default_status', 'default_priority', 'order')
    list_filter = ('default_status', 'default_priority', 'project_template')
    search_fields = ('title', 'description')
    
@admin.register(ProjectSchedule)
class ProjectScheduleAdmin(admin.ModelAdmin):
    list_display = ('project', 'estimated_start_date', 'estimated_end_date', 'progress', 'is_baseline')
    list_filter = ('is_baseline',)
    search_fields = ('project__title', 'description')
    date_hierarchy = 'created_at'

@admin.register(ProjectPhase)
class ProjectPhaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'schedule', 'start_date', 'end_date', 'order', 'progress')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('schedule', 'order')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'schedule', 'phase', 'due_date', 'status', 'completion_date')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    date_hierarchy = 'due_date'
