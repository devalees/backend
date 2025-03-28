from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import DataTransferModel
from .transfer import DataTransfer
from .mixins import DataTransferMixin
import pandas as pd
from io import BytesIO

@admin.register(DataTransferModel)
class DataTransferAdmin(DataTransferMixin, admin.ModelAdmin):
    list_display = ('name', 'transfer_type', 'file_type', 'source_model', 
                   'status', 'records_processed', 'records_failed', 'created_at', 
                   'duration_display', 'status_badge', 'action_buttons')
    
    list_filter = ('status', 'transfer_type', 'file_type', 'created_at')
    search_fields = ('name', 'source_model', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'duration')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'transfer_type', 'file_type', 'source_model')
        }),
        ('File Details', {
            'fields': ('file_path', 'field_mapping')
        }),
        ('Status & Results', {
            'fields': ('status', 'records_processed', 'records_failed', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'duration'),
            'classes': ('collapse',)
        })
    )

    def duration_display(self, obj):
        """Format duration for display"""
        duration = obj.duration
        if duration:
            # Convert duration to a readable format
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            seconds = duration.seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "-"
    duration_display.short_description = "Duration"

    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            'pending': '#FFA500',    # Orange
            'processing': '#1E90FF', # Blue
            'completed': '#32CD32',  # Green
            'failed': '#FF0000'      # Red
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#808080'),
            obj.status.upper()
        )
    status_badge.short_description = "Status"

    def action_buttons(self, obj):
        """Display action buttons"""
        return format_html(
            '<a class="button" href="{}">Export Sample</a>&nbsp;'
            '<a class="button" href="{}">Import Data</a>',
            f'/admin/data_transfer/datatransfermodel/{obj.id}/export-sample/',
            f'/admin/data_transfer/datatransfermodel/{obj.id}/import-data/'
        )
    action_buttons.short_description = "Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:transfer_id>/export-sample/',
                self.admin_site.admin_view(self.export_sample),
                name='export-sample',
            ),
            path(
                '<int:transfer_id>/import-data/',
                self.admin_site.admin_view(self.import_data),
                name='import-data',
            ),
        ]
        return custom_urls + urls

    def export_sample(self, request, transfer_id):
        """Export sample data based on the model"""
        try:
            transfer = DataTransferModel.objects.get(id=transfer_id)
            # Create sample data
            sample_data = {
                'name': ['Sample Name 1', 'Sample Name 2'],
                'email': ['sample1@example.com', 'sample2@example.com'],
                'age': [25, 30]
            }
            df = pd.DataFrame(sample_data)
            
            # Create response
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="sample_{transfer.file_type}.xlsx"'
            
            # Write to response
            df.to_excel(response, index=False)
            return response
        except Exception as e:
            messages.error(request, f'Error exporting sample: {str(e)}')
            return redirect('admin:data_transfer_datatransfermodel_changelist')

    def import_data(self, request, transfer_id):
        """Import data using the DataTransfer class"""
        try:
            transfer = DataTransferModel.objects.get(id=transfer_id)
            transfer.mark_as_processing()
            
            # Get the model class dynamically
            model_class = self._get_model_class(transfer.source_model)
            if not model_class:
                raise ValueError(f"Model {transfer.source_model} not found")
            
            # Create DataTransfer instance
            data_transfer = DataTransfer(model_class)
            
            # Import data based on file type
            if transfer.file_type == 'csv':
                records = data_transfer.import_csv(transfer.file_path)
            else:  # excel
                records = data_transfer.import_excel(transfer.file_path)
            
            # Update transfer status
            transfer.mark_as_completed(len(records))
            messages.success(request, f'Successfully imported {len(records)} records')
        except Exception as e:
            transfer.mark_as_failed(str(e))
            messages.error(request, f'Error importing data: {str(e)}')
        
        return redirect('admin:data_transfer_datatransfermodel_changelist')

    def _get_model_class(self, model_name):
        """Get model class from string"""
        from django.apps import apps
        try:
            app_label, model = model_name.split('.')
            return apps.get_model(app_label, model)
        except:
            return None
