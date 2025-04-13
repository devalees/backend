from typing import Dict, Any, List, Optional, Type
from django.db import models
from django.core.exceptions import ValidationError, FieldDoesNotExist
from .base import BaseAggregatableModel
from .aggregations import aggregation_registry

class AggregationFieldValidator:
    """Validates fields used in aggregations."""
    
    def validate(self, field_name: str, model: Type[BaseAggregatableModel]) -> bool:
        """
        Validate that a field can be used for aggregation.
        
        Args:
            field_name: The name of the field to validate
            model: The model class containing the field
            
        Returns:
            True if the field is valid for aggregation
            
        Raises:
            ValidationError: If the field is not valid for aggregation
        """
        # Check if field exists
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            raise ValidationError(f"Field '{field_name}' does not exist on model {model.__name__}")
        
        # Get aggregatable fields from model
        aggregatable_fields = model.get_aggregatable_fields()
        
        # Check if field is aggregatable
        if field_name not in aggregatable_fields and field_name != 'id':
            raise ValidationError(f"Field '{field_name}' is not aggregatable")
        
        return True

class AggregationTypeValidator:
    """Validates aggregation types."""
    
    def __init__(self):
        self.numeric_types = {'sum', 'avg', 'min', 'max'}
        self.all_types = self.numeric_types | {'count'}
    
    def validate(self, agg_type: str, field_name: str, model: Type[BaseAggregatableModel] = None) -> bool:
        """
        Validate that an aggregation type is valid for a field.
        
        Args:
            agg_type: The type of aggregation to validate
            field_name: The name of the field to validate against
            model: The model class containing the field
            
        Returns:
            True if the aggregation type is valid
            
        Raises:
            ValidationError: If the aggregation type is not valid
        """
        # Check if aggregation type exists
        if agg_type not in aggregation_registry.aggregations:
            raise ValidationError(f"Invalid aggregation type: {agg_type}")
        
        # Count is valid for any field
        if agg_type == 'count':
            return True
        
        # For other types, check if they're valid numeric aggregations
        if agg_type in self.numeric_types and model:
            # Get the field from the model
            try:
                field = model._meta.get_field(field_name)
                if not isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                    raise ValidationError(f"Field '{field_name}' is not numeric and cannot be used with {agg_type} aggregation")
            except FieldDoesNotExist:
                raise ValidationError(f"Field '{field_name}' does not exist")
            
        return True

class AggregationGroupValidator:
    """Validates group by fields."""
    
    def validate(self, group_by: Optional[List[str]], model: Type[BaseAggregatableModel]) -> bool:
        """
        Validate that group by fields are valid.
        
        Args:
            group_by: List of fields to group by, or None
            model: The model class containing the fields
            
        Returns:
            True if the group by fields are valid
            
        Raises:
            ValidationError: If any group by field is not valid
        """
        # None or empty list is valid (no grouping)
        if not group_by:
            return True
        
        # Check that all group by fields are strings
        if not all(isinstance(field, str) for field in group_by):
            raise ValidationError("All group by fields must be strings")
        
        # Check that all fields exist on the model
        model_fields = {f.name for f in model._meta.get_fields()}
        invalid_fields = [field for field in group_by if field not in model_fields]
        if invalid_fields:
            raise ValidationError(f"Invalid group by fields: {', '.join(invalid_fields)}")
        
        return True

class AggregationValidator:
    """Main validator for aggregation configurations."""
    
    def __init__(self):
        self.field_validator = AggregationFieldValidator()
        self.type_validator = AggregationTypeValidator()
        self.group_validator = AggregationGroupValidator()
    
    def validate(self, config: Dict[str, Any], model: Type[BaseAggregatableModel]) -> bool:
        """
        Validate a complete aggregation configuration.
        
        Args:
            config: The aggregation configuration to validate
            model: The model class to validate against
            
        Returns:
            True if the configuration is valid
            
        Raises:
            ValidationError: If the configuration is not valid
        """
        # Check that config has fields
        if not config or 'fields' not in config:
            raise ValidationError("Configuration must include 'fields'")
        
        # Check that fields is not empty
        if not config['fields']:
            raise ValidationError("Configuration must include at least one field")
        
        # Validate each field and its aggregation types
        for field_name, agg_types in config['fields'].items():
            # Validate the field
            self.field_validator.validate(field_name, model)
            
            # Convert single aggregation type to list
            if isinstance(agg_types, str):
                agg_types = [agg_types]
            
            # Validate each aggregation type
            for agg_type in agg_types:
                self.type_validator.validate(agg_type, field_name, model)
        
        # Validate group by if present
        if 'group_by' in config:
            self.group_validator.validate(config['group_by'], model)
        
        return True 