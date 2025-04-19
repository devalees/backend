from django.contrib import admin
from django.utils.html import format_html
from .models import Document, DocumentVersion, DocumentClassification, DocumentTag
from Apps.rbac.admin import OrganizationIsolationAdminMixin

@admin.register(Document)
class DocumentAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'status', 'user', 'organization', 'updated_at', 'show_filter_config')
    list_filter = ('status', 'user', 'classification', 'tags', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'show_filter_config', 'show_aggregation_config')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status', 'file')
        }),
        ('Classification', {
            'fields': ('classification', 'tags')
        }),
        ('Organization', {
            'fields': ('organization', 'is_active')
        }),
        ('Metadata', {
            'fields': ('user', 'created_at', 'updated_at', 'is_deleted')
        }),
        ('Filtering & Aggregation', {
            'fields': ('show_filter_config', 'show_aggregation_config'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new document
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def show_filter_config(self, obj):
        """Display the filter configuration for this model."""
        if not hasattr(obj, 'FilterConfig'):
            return "No filter configuration defined"
        
        config = []
        for field_type, fields in vars(obj.FilterConfig).items():
            if not field_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{field_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_filter_config.short_description = "Filter Configuration"
    
    def show_aggregation_config(self, obj):
        """Display the aggregation configuration for this model."""
        if not hasattr(obj, 'AggregationConfig'):
            return "No aggregation configuration defined"
        
        config = []
        for agg_type, fields in vars(obj.AggregationConfig).items():
            if not agg_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{agg_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_aggregation_config.short_description = "Aggregation Configuration"

@admin.register(DocumentVersion)
class DocumentVersionAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('document', 'version_number', 'branch_name', 'user', 'organization', 'created_at', 'show_filter_config')
    list_filter = ('document', 'user', 'branch_name', 'is_current', 'is_active')
    search_fields = ('document__title', 'comment')
    readonly_fields = ('created_at', 'updated_at', 'show_filter_config', 'show_aggregation_config')
    fieldsets = (
        (None, {
            'fields': ('document', 'version_number', 'branch_name', 'is_current')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Versioning', {
            'fields': ('parent_version', 'merged_to')
        }),
        ('Organization', {
            'fields': ('organization', 'is_active')
        }),
        ('Metadata', {
            'fields': ('user', 'comment', 'created_at', 'updated_at')
        }),
        ('Filtering & Aggregation', {
            'fields': ('show_filter_config', 'show_aggregation_config'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change and not hasattr(obj, 'organization'):
            obj.organization = obj.document.organization
        super().save_model(request, obj, form, change)
    
    def show_filter_config(self, obj):
        """Display the filter configuration for this model."""
        if not hasattr(obj, 'FilterConfig'):
            return "No filter configuration defined"
        
        config = []
        for field_type, fields in vars(obj.FilterConfig).items():
            if not field_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{field_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_filter_config.short_description = "Filter Configuration"
    
    def show_aggregation_config(self, obj):
        """Display the aggregation configuration for this model."""
        if not hasattr(obj, 'AggregationConfig'):
            return "No aggregation configuration defined"
        
        config = []
        for agg_type, fields in vars(obj.AggregationConfig).items():
            if not agg_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{agg_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_aggregation_config.short_description = "Aggregation Configuration"

@admin.register(DocumentClassification)
class DocumentClassificationAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'parent', 'organization', 'created_at', 'show_filter_config')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'show_filter_config', 'show_aggregation_config')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent')
        }),
        ('Organization', {
            'fields': ('organization', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Filtering & Aggregation', {
            'fields': ('show_filter_config', 'show_aggregation_config'),
            'classes': ('collapse',)
        }),
    )
    
    def show_filter_config(self, obj):
        """Display the filter configuration for this model."""
        if not hasattr(obj, 'FilterConfig'):
            return "No filter configuration defined"
        
        config = []
        for field_type, fields in vars(obj.FilterConfig).items():
            if not field_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{field_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_filter_config.short_description = "Filter Configuration"
    
    def show_aggregation_config(self, obj):
        """Display the aggregation configuration for this model."""
        if not hasattr(obj, 'AggregationConfig'):
            return "No aggregation configuration defined"
        
        config = []
        for agg_type, fields in vars(obj.AggregationConfig).items():
            if not agg_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{agg_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_aggregation_config.short_description = "Aggregation Configuration"

@admin.register(DocumentTag)
class DocumentTagAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'color', 'organization', 'created_at', 'show_filter_config')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'show_filter_config', 'show_aggregation_config')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'color')
        }),
        ('Organization', {
            'fields': ('organization', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Filtering & Aggregation', {
            'fields': ('show_filter_config', 'show_aggregation_config'),
            'classes': ('collapse',)
        }),
    )
    
    def show_filter_config(self, obj):
        """Display the filter configuration for this model."""
        if not hasattr(obj, 'FilterConfig'):
            return "No filter configuration defined"
        
        config = []
        for field_type, fields in vars(obj.FilterConfig).items():
            if not field_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{field_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_filter_config.short_description = "Filter Configuration"
    
    def show_aggregation_config(self, obj):
        """Display the aggregation configuration for this model."""
        if not hasattr(obj, 'AggregationConfig'):
            return "No aggregation configuration defined"
        
        config = []
        for agg_type, fields in vars(obj.AggregationConfig).items():
            if not agg_type.startswith('_') and isinstance(fields, list):
                config.append(f"<strong>{agg_type}:</strong> {', '.join(fields)}")
        
        return format_html("<br>".join(config))
    show_aggregation_config.short_description = "Aggregation Configuration"
