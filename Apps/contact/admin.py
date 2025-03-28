from django.contrib import admin
from .models import Contact, ContactCategory

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'category', 'created_at', 'updated_at')
    list_filter = ('category', 'contact_type', 'created_at', 'updated_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'company')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ContactCategory)
class ContactCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
