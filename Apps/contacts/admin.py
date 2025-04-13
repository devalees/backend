from django.contrib import admin
from .models import Contact, ContactGroup, ContactTemplate, ContactGroupTemplate, ContactMonitoring, ContactGroupMonitoring, Communication, CommunicationTemplate, CommunicationMonitoring, ContactList, ContactListTemplate, ContactSegment

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'organization', 'department', 'team', 'is_active')
    list_filter = ('is_active', 'organization', 'department', 'team')
    search_fields = ('name', 'email', 'phone')

@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'parent', 'is_active')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'description')

@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'contact', 'organization', 'communication_type', 'status', 'created_at', 'is_active')
    list_filter = ('is_active', 'communication_type', 'status', 'organization')
    search_fields = ('subject', 'message')
    date_hierarchy = 'created_at'
    
@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'communication_type', 'is_active')
    list_filter = ('is_active', 'communication_type', 'organization')
    search_fields = ('name', 'description', 'subject_template', 'message_template')
    
@admin.register(CommunicationMonitoring)
class CommunicationMonitoringAdmin(admin.ModelAdmin):
    list_display = ('communication', 'activity_type', 'user', 'organization', 'created_at')
    list_filter = ('activity_type', 'organization')
    search_fields = ('description', 'ip_address')
    date_hierarchy = 'created_at'

@admin.register(ContactList)
class ContactListAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active')
    list_filter = ('is_active', 'organization')
    search_fields = ('name', 'description')
    filter_horizontal = ('contacts',)

@admin.register(ContactListTemplate)
class ContactListTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'version', 'parent', 'is_active')
    list_filter = ('is_active', 'organization', 'version')
    search_fields = ('name', 'description')

@admin.register(ContactSegment)
class ContactSegmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_list', 'is_active')
    list_filter = ('is_active', 'contact_list__organization')
    search_fields = ('name', 'description')
