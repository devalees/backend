from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ImportExportConfig, ImportExportLog


@admin.register(ImportExportConfig)
class ImportExportConfigAdmin(admin.ModelAdmin):
    """Admin interface for ImportExportConfig model."""
    list_display = ('name', 'content_type', 'is_active', 'created_by', 'created_at')
    list_filter = ('content_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('content_type', 'name', 'description')
        }),
        (_('Configuration'), {
            'fields': ('field_mapping', 'is_active')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Save model with user tracking."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImportExportLog)
class ImportExportLogAdmin(admin.ModelAdmin):
    """Admin interface for ImportExportLog model."""
    list_display = (
        'file_name', 'config', 'operation', 'status',
        'records_processed', 'success_rate', 'performed_by'
    )
    list_filter = ('operation', 'status', 'created_at')
    search_fields = ('file_name', 'error_message')
    readonly_fields = (
        'operation', 'status', 'file_name', 'error_message',
        'records_processed', 'records_succeeded', 'records_failed',
        'performed_by', 'created_at', 'updated_at'
    )
    fieldsets = (
        (None, {
            'fields': ('config', 'operation', 'status', 'file_name')
        }),
        (_('Results'), {
            'fields': (
                'records_processed', 'records_succeeded',
                'records_failed', 'error_message'
            )
        }),
        (_('Audit'), {
            'fields': ('performed_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Disable manual creation of logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of logs."""
        return False
