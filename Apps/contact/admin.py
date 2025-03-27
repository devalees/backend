from django.contrib import admin
from .models import Contact, ContactCategory

@admin.register(ContactCategory)
class ContactCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'company', 'category', 'created_at')
    list_filter = ('created_at', 'category', 'company')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'company', 'message')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    autocomplete_fields = ['category']
