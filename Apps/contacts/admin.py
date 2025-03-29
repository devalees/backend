from django.contrib import admin
from .models import Contact, ContactGroup

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'organization', 'department', 'team', 'is_active')
    list_filter = ('organization', 'department', 'team', 'is_active')
    search_fields = ('name', 'email', 'phone', 'organization__name', 'department__name', 'team__name')
    ordering = ('name',)
    raw_id_fields = ('organization', 'department', 'team')

@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    filter_horizontal = ('contacts',)
