from django.contrib import admin
from .models import Document, DocumentVersion, DocumentClassification, DocumentTag

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'user', 'updated_at')
    list_filter = ('status', 'user', 'classification', 'tags')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'status')
        }),
        ('Classification', {
            'fields': ('classification', 'tags')
        }),
        ('Metadata', {
            'fields': ('user', 'updated_by', 'created_at', 'updated_at', 'is_deleted')
        }),
    )

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('document', 'version_number', 'user', 'created_at')
    list_filter = ('document', 'user')
    search_fields = ('document__title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('document', 'version_number', 'is_current')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size', 'mime_type')
        }),
        ('Metadata', {
            'fields': ('user', 'comment', 'created_at', 'updated_at')
        }),
    )

@admin.register(DocumentClassification)
class DocumentClassificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'color')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
