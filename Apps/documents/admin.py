from django.contrib import admin
from .models import Document, DocumentVersion, DocumentClassification, DocumentTag
from Apps.rbac.admin import OrganizationIsolationAdminMixin

@admin.register(Document)
class DocumentAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'status', 'user', 'organization', 'updated_at')
    list_filter = ('status', 'user', 'classification', 'tags', 'is_active')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
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
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new document
            obj.user = request.user
        super().save_model(request, obj, form, change)

@admin.register(DocumentVersion)
class DocumentVersionAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('document', 'version_number', 'branch_name', 'user', 'organization', 'created_at')
    list_filter = ('document', 'user', 'branch_name', 'is_current', 'is_active')
    search_fields = ('document__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
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
    )
    
    def save_model(self, request, obj, form, change):
        if not change and not hasattr(obj, 'organization'):
            obj.organization = obj.document.organization
        super().save_model(request, obj, form, change)

@admin.register(DocumentClassification)
class DocumentClassificationAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'parent', 'organization', 'created_at')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
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
    )

@admin.register(DocumentTag)
class DocumentTagAdmin(OrganizationIsolationAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'color', 'organization', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
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
    )
