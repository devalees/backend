from django.contrib import admin
from .models import FieldControl

@admin.register(FieldControl)
class FieldControlAdmin(admin.ModelAdmin):
    list_display = ('field_name', 'module_id', 'field_type', 'is_active', 'created_at')
    list_filter = ('field_type', 'is_active', 'module_id', 'created_at')
    search_fields = ('field_name', 'module_id', 'field_type')
    readonly_fields = ('field_type', 'created_at', 'updated_at')
    ordering = ('module_id', 'field_name')

    fieldsets = (
        ('Field Information', {
            'fields': ('field_name', 'module_id', 'field_type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def field_name(self, obj):
        """Display the module name as field name"""
        return obj.module_name
    field_name.short_description = 'Field Name'
    field_name.admin_order_field = 'module_name'

    def field_count(self, obj):
        """Display the number of tracked fields"""
        return len(obj.get_tracked_fields())
    field_count.short_description = 'Number of Fields'

    def available_fields(self, obj):
        """Display all available fields in a readable format"""
        fields = obj.get_model_fields()
        return ', '.join(fields) if fields else 'No fields available'
    available_fields.short_description = 'Available Fields'

    def get_fieldsets(self, request, obj=None):
        """Customize field organization in the edit form"""
        return (
            ('Model Information', {
                'fields': ('module_id', 'module_name', 'full_name', 'is_active')
            }),
            ('Fields Information', {
                'fields': ('fields_list', 'available_fields'),
                'description': 'Fields are automatically tracked. The fields list shows currently tracked fields.'
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        """Make field_type readonly only if object already exists"""
        if obj:  # Editing an existing object
            return self.readonly_fields
        return ('created_at', 'updated_at')
