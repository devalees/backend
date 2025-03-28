from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .transfer import DataTransfer
import pandas as pd
from io import BytesIO
from django.db.models import Model
from django.core.exceptions import FieldDoesNotExist
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.core.exceptions import ValidationError

class DataTransferMixin:
    """Mixin to add import/export functionality to any model's admin"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:obj_id>/export-sample/',
                self.admin_site.admin_view(self.export_sample),
                name='export-sample',
            ),
            path(
                '<int:obj_id>/import-data/',
                self.admin_site.admin_view(self.import_data),
                name='import-data',
            ),
        ]
        return custom_urls + urls

    def export_sample(self, request, obj_id):
        """Export sample data based on the model"""
        try:
            obj = self.model.objects.get(id=obj_id)
            # Get all fields from the model
            fields = [f.name for f in self.model._meta.fields]
            
            # Create sample data with one row
            sample_data = {field: ['Sample Value'] for field in fields}
            df = pd.DataFrame(sample_data)
            
            # Create response
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="sample_{self.model._meta.model_name}.xlsx"'
            
            # Write to response
            df.to_excel(response, index=False)
            return response
        except Exception as e:
            messages.error(request, f'Error exporting sample: {str(e)}')
            return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')

    def import_data(self, request, obj_id):
        """Import data using the DataTransfer class"""
        try:
            obj = self.model.objects.get(id=obj_id)
            # Create DataTransfer instance
            data_transfer = DataTransfer(self.model)
            
            # Get the file from the request
            if 'file' not in request.FILES:
                raise ValueError("No file uploaded")
            
            file = request.FILES['file']
            file_extension = file.name.split('.')[-1].lower()
            
            # Import data based on file type
            if file_extension == 'csv':
                records = data_transfer.import_csv(file)
            elif file_extension in ['xlsx', 'xls']:
                records = data_transfer.import_excel(file)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            messages.success(request, f'Successfully imported {len(records)} records')
        except Exception as e:
            messages.error(request, f'Error importing data: {str(e)}')
        
        return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')

    def action_buttons(self, obj):
        """Display action buttons"""
        return format_html(
            '<div style="display: flex; gap: 8px;">'
            '<a class="button" href="{}" style="background-color: #79aec8; padding: 5px 10px; '
            'border-radius: 4px; color: white; text-decoration: none;">Export Sample</a>'
            '<a class="button" href="{}" style="background-color: #417690; padding: 5px 10px; '
            'border-radius: 4px; color: white; text-decoration: none;">Import Data</a>'
            '</div>',
            f'/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{obj.id}/export-sample/',
            f'/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{obj.id}/import-data/'
        )
    action_buttons.short_description = "Actions"

class DynamicDownloadMixin:
    """
    A mixin to add dynamic download functionality to any model.
    This mixin provides methods to download model data in various formats.
    """
    
    ALLOWED_EXTENSIONS = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel'
    }

    @classmethod
    def validate_file_type(cls, file) -> bool:
        """Validate if the file type is allowed"""
        if not file:
            raise ValidationError("No file was submitted.")
            
        # Get file extension
        extension = file.name.split('.')[-1].lower()
        
        if extension not in cls.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"Invalid file type. Allowed types are: {', '.join(cls.ALLOWED_EXTENSIONS.keys())}"
            )
        return True

    def get_exportable_fields(self) -> List[str]:
        """Get list of fields that can be exported"""
        exclude_fields = ['password', 'id', 'created_at', 'updated_at']
        fields = []
        
        for field in self._meta.fields:
            if field.name not in exclude_fields:
                fields.append(field.name)
        return fields

    def get_field_verbose_names(self) -> Dict[str, str]:
        """Get verbose names for fields"""
        return {
            field.name: field.verbose_name.title() 
            for field in self._meta.fields 
            if field.name in self.get_exportable_fields()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        data = {}
        for field in self.get_exportable_fields():
            try:
                value = getattr(self, field)
                # Handle foreign key relationships
                if isinstance(value, Model):
                    value = str(value)
                data[field] = value
            except (AttributeError, FieldDoesNotExist):
                data[field] = None
        return data

    @classmethod
    def get_queryset_as_dataframe(cls, queryset=None) -> pd.DataFrame:
        """Convert queryset to pandas DataFrame"""
        if queryset is None:
            queryset = cls.objects.all()
            
        data = [obj.to_dict() for obj in queryset]
        df = pd.DataFrame(data)
        
        # Rename columns to verbose names
        verbose_names = cls._meta.model().get_field_verbose_names()
        df = df.rename(columns=verbose_names)
        
        return df

    @classmethod
    def download_as_excel(cls, queryset=None, filename: Optional[str] = None) -> HttpResponse:
        """Download data as Excel file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{cls._meta.model_name}_{timestamp}.xlsx"
            
        df = cls.get_queryset_as_dataframe(queryset)
        
        # Create Excel response
        response = HttpResponse(content_type=cls.ALLOWED_EXTENSIONS['xlsx'])
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Write to Excel with formatting
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, len(str(value)) + 5)
                
        return response

    @classmethod
    def download_as_csv(cls, queryset=None, filename: Optional[str] = None) -> HttpResponse:
        """Download data as CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{cls._meta.model_name}_{timestamp}.csv"
            
        df = cls.get_queryset_as_dataframe(queryset)
        
        # Create CSV response
        response = HttpResponse(content_type=cls.ALLOWED_EXTENSIONS['csv'])
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Write to CSV
        df.to_csv(response, index=False)
        return response

    @classmethod
    def import_data(cls, file) -> int:
        """Import data from CSV or Excel file"""
        try:
            # Validate file type
            cls.validate_file_type(file)
            
            # Get file extension
            extension = file.name.split('.')[-1].lower()
            
            # Read file based on type, treating phone numbers as strings
            if extension == 'csv':
                df = pd.read_csv(file, dtype={'phone': str})
            else:  # xlsx or xls
                df = pd.read_excel(file, dtype={'phone': str})
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Create objects
            created_objects = []
            for record in records:
                # Format phone number if present
                if 'phone' in record and record['phone']:
                    phone = str(record['phone'])
                    # Ensure leading zeros are preserved
                    if phone.isdigit():
                        phone = '+' + phone
                    record['phone'] = phone
                
                # Create and save object with validation
                obj = cls(**record)
                obj.skip_validation = True
                obj.save()
                created_objects.append(obj)
            
            return len(created_objects)
            
        except Exception as e:
            raise ValidationError(f"Error importing data: {str(e)}")

    @classmethod
    def download_as_json(cls, queryset=None, filename: Optional[str] = None) -> HttpResponse:
        """Download data as JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{cls._meta.model_name}_{timestamp}.json"
            
        df = cls.get_queryset_as_dataframe(queryset)
        
        # Create JSON response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Write to JSON
        df.to_json(response, orient='records')
        return response 