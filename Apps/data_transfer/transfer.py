import pandas as pd
import csv
from io import StringIO, BytesIO
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from typing import Dict, List, Any, Callable, Optional

class DataTransfer:
    """
    A dynamic data transfer class that can import/export data from/to CSV and Excel files
    for any Django model.
    """
    
    def __init__(
        self,
        model: models.Model,
        field_mapping: Optional[Dict[str, str]] = None,
        validation_rules: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize the DataTransfer class.
        
        Args:
            model: The Django model class to work with
            field_mapping: Optional dictionary mapping file columns to model fields
            validation_rules: Optional dictionary of field validation functions
        """
        self.model = model
        self.field_mapping = field_mapping or {}
        self.validation_rules = validation_rules or {}
        
        # Get model fields
        self.model_fields = {
            field.name: field for field in self.model._meta.fields
            if not isinstance(field, (models.AutoField, models.BigAutoField))
        }
        
        # Create reverse mapping for export
        self.reverse_mapping = {
            v: k for k, v in self.field_mapping.items()
        }

    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data using custom validation rules.
        
        Args:
            data: Dictionary of field values to validate
            
        Returns:
            Validated data dictionary
            
        Raises:
            ValueError: If validation fails
        """
        validated_data = {}
        for field, value in data.items():
            if field in self.validation_rules:
                try:
                    validated_data[field] = self.validation_rules[field](value)
                except ValueError as e:
                    raise ValueError(f"Validation failed for field '{field}': {str(e)}")
            else:
                # Default validation for email field
                if field == 'email' and not self._is_valid_email(value):
                    raise ValueError(f"Invalid email format: {value}")
                validated_data[field] = value
        return validated_data

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email string to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    def _map_fields(self, data: Dict[str, Any], reverse: bool = False) -> Dict[str, Any]:
        """
        Map file columns to model fields or vice versa.
        
        Args:
            data: Dictionary of field values to map
            reverse: If True, map from model fields to file columns
            
        Returns:
            Mapped data dictionary
        """
        mapping = self.reverse_mapping if reverse else self.field_mapping
        return {mapping.get(k, k): v for k, v in data.items()}

    def import_csv(self, file: UploadedFile) -> List[models.Model]:
        """
        Import data from a CSV file.
        
        Args:
            file: CSV file to import
            
        Returns:
            List of created model instances
            
        Raises:
            ValueError: If file is empty or data is invalid
        """
        if not file.size:
            raise ValueError("File is empty")
            
        content = file.read().decode('utf-8')
        if not content.strip():
            raise ValueError("File contains no data")
            
        reader = csv.DictReader(StringIO(content))
        created_objects = []
        
        for row in reader:
            # Map file columns to model fields
            mapped_data = self._map_fields(row)
            
            # Validate data
            validated_data = self._validate_data(mapped_data)
            
            # Create model instance
            try:
                instance = self.model.objects.create(**validated_data)
                created_objects.append(instance)
            except Exception as e:
                raise ValueError(f"Failed to create model instance: {str(e)}")
                
        return created_objects

    def import_excel(self, file: UploadedFile) -> List[models.Model]:
        """
        Import data from an Excel file.
        
        Args:
            file: Excel file to import
            
        Returns:
            List of created model instances
            
        Raises:
            ValueError: If file is empty or data is invalid
        """
        if not file.size:
            raise ValueError("File is empty")
            
        try:
            df = pd.read_excel(file)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")
            
        if df.empty:
            raise ValueError("File contains no data")
            
        created_objects = []
        
        for _, row in df.iterrows():
            # Convert row to dictionary
            data = row.to_dict()
            
            # Map file columns to model fields
            mapped_data = self._map_fields(data)
            
            # Validate data
            validated_data = self._validate_data(mapped_data)
            
            # Create model instance
            try:
                instance = self.model.objects.create(**validated_data)
                created_objects.append(instance)
            except Exception as e:
                raise ValueError(f"Failed to create model instance: {str(e)}")
                
        return created_objects

    def export_csv(self) -> str:
        """
        Export model data to CSV format.
        
        Returns:
            CSV string
        """
        if not self.model.objects.exists():
            return ""
            
        # Get all model instances
        queryset = self.model.objects.all()
        
        # Get field names
        field_names = list(self.model_fields.keys())
        
        # Create CSV output
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=field_names)
        
        writer.writeheader()
        for instance in queryset:
            # Convert instance to dictionary
            data = {
                field: getattr(instance, field)
                for field in field_names
            }
            
            # Map model fields to file columns
            mapped_data = self._map_fields(data, reverse=True)
            
            writer.writerow(mapped_data)
            
        return output.getvalue()

    def export_excel(self) -> bytes:
        """
        Export model data to Excel format.
        
        Returns:
            Excel file bytes
        """
        if not self.model.objects.exists():
            return b""
            
        # Get all model instances
        queryset = self.model.objects.all()
        
        # Get field names
        field_names = list(self.model_fields.keys())
        
        # Create DataFrame
        data = []
        for instance in queryset:
            # Convert instance to dictionary
            row_data = {
                field: getattr(instance, field)
                for field in field_names
            }
            
            # Map model fields to file columns
            mapped_data = self._map_fields(row_data, reverse=True)
            
            data.append(mapped_data)
            
        df = pd.DataFrame(data)
        
        # Create Excel output
        output = BytesIO()
        df.to_excel(output, index=False)
        
        return output.getvalue() 