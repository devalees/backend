from django.contrib import admin
from django.http import HttpResponse
from django.contrib import messages
from .models import Contact, ContactCategory

@admin.register(ContactCategory)
class ContactCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    actions = ['download_as_excel', 'download_as_csv']

    def download_as_excel(self, request, queryset):
        """Download selected categories as Excel"""
        return ContactCategory.download_as_excel(queryset)
    download_as_excel.short_description = "Download selected categories as Excel"

    def download_as_csv(self, request, queryset):
        """Download selected categories as CSV"""
        return ContactCategory.download_as_csv(queryset)
    download_as_csv.short_description = "Download selected categories as CSV"

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'category')
    list_filter = ('category',)
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    actions = ['download_as_excel', 'download_as_csv']

    def download_as_excel(self, request, queryset):
        """Download selected contacts as Excel"""
        return Contact.download_as_excel(queryset)
    download_as_excel.short_description = "Download selected contacts as Excel"

    def download_as_csv(self, request, queryset):
        """Download selected contacts as CSV"""
        return Contact.download_as_csv(queryset)
    download_as_csv.short_description = "Download selected contacts as CSV"
