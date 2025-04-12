from typing import Any, Dict, List, Union, Set
from datetime import datetime, date, time
import re

class FilterValidationError(Exception):
    """
    Exception raised for filter validation errors.
    """
    pass

class FieldTypeValidator:
    """
    Validates field types for filters.
    """
    def __init__(self):
        self.valid_field_types = {
            # Text field types
            'char', 'text', 'email', 'url',
            # Numeric field types
            'integer', 'decimal', 'float',
            # Date field types
            'date', 'datetime', 'time',
            # Boolean field type
            'boolean',
            # Choice field type
            'choice',
            # Related field type
            'related'
        }
    
    def validate(self, field_name: str, field_type: str) -> bool:
        """
        Validate that the field type is supported.
        
        Args:
            field_name: The name of the field
            field_type: The type of the field
            
        Returns:
            True if the field type is valid
            
        Raises:
            FilterValidationError: If the field type is not supported
        """
        if field_type not in self.valid_field_types:
            raise FilterValidationError(f"Invalid field type: {field_type}")
        return True

class OperatorValidator:
    """
    Validates operators for filters.
    """
    def __init__(self):
        self.valid_operators = {
            # Text operators
            'char': {'contains', 'startswith', 'endswith', 'regex', 'exact', 'iexact', 'in'},
            'text': {'contains', 'startswith', 'endswith', 'regex', 'exact', 'iexact', 'in'},
            'email': {'contains', 'startswith', 'endswith', 'regex', 'exact', 'iexact', 'in'},
            'url': {'contains', 'startswith', 'endswith', 'regex', 'exact', 'iexact', 'in'},
            
            # Numeric operators
            'integer': {'exact', 'gt', 'gte', 'lt', 'lte', 'range', 'in'},
            'decimal': {'exact', 'gt', 'gte', 'lt', 'lte', 'range', 'in'},
            'float': {'exact', 'gt', 'gte', 'lt', 'lte', 'range', 'in'},
            
            # Date operators
            'date': {'exact', 'gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day', 'week_day'},
            'datetime': {'exact', 'gt', 'gte', 'lt', 'lte', 'range', 'year', 'month', 'day', 'week_day'},
            
            # Time operators
            'time': {'exact', 'gt', 'gte', 'lt', 'lte', 'hour', 'minute', 'second'},
            
            # Boolean operators
            'boolean': {'exact', 'isnull'},
            
            # Choice operators
            'choice': {'exact', 'in'},
            
            # Related operators
            'related': {'exact', 'in', 'isnull'}
        }
    
    def validate(self, field_type: str, operator: str) -> bool:
        """
        Validate that the operator is supported for the given field type.
        
        Args:
            field_type: The type of the field
            operator: The operator to validate
            
        Returns:
            True if the operator is valid for the field type
            
        Raises:
            FilterValidationError: If the operator is not supported for the field type
        """
        if field_type not in self.valid_operators:
            raise FilterValidationError(f"Invalid field type: {field_type}")
        
        if operator not in self.valid_operators[field_type]:
            raise FilterValidationError(f"Invalid operator '{operator}' for field type '{field_type}'")
        
        return True

class ValueValidator:
    """
    Validates values for filters.
    """
    def validate(self, field_type: str, operator: str, value: Any) -> bool:
        """
        Validate that the value is appropriate for the given field type and operator.
        
        Args:
            field_type: The type of the field
            operator: The operator being used
            value: The value to validate
            
        Returns:
            True if the value is valid
            
        Raises:
            FilterValidationError: If the value is not valid for the field type and operator
        """
        # Handle null checks
        if operator == 'isnull':
            if not isinstance(value, bool):
                raise FilterValidationError(f"Invalid value for isnull operator: {value}")
            return True
        
        # Handle text field types
        if field_type in {'char', 'text', 'email', 'url'}:
            if operator in {'contains', 'startswith', 'endswith', 'exact', 'iexact'}:
                if not isinstance(value, str):
                    raise FilterValidationError(f"Invalid value for text operator: {value}")
            elif operator == 'regex':
                if not isinstance(value, str):
                    raise FilterValidationError(f"Invalid value for regex operator: {value}")
                try:
                    re.compile(value)
                except re.error:
                    raise FilterValidationError(f"Invalid regex pattern: {value}")
            elif operator == 'in':
                if not isinstance(value, (list, tuple, set)):
                    raise FilterValidationError(f"Invalid value for 'in' operator: {value}")
                if not all(isinstance(item, str) for item in value):
                    raise FilterValidationError(f"All items in 'in' list must be strings")
        
        # Handle numeric field types
        elif field_type in {'integer', 'decimal', 'float'}:
            if operator in {'exact', 'gt', 'gte', 'lt', 'lte'}:
                if not isinstance(value, (int, float)):
                    raise FilterValidationError(f"Invalid value for numeric operator: {value}")
            elif operator == 'range':
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    raise FilterValidationError(f"Invalid value for range operator: {value}")
                if not all(isinstance(item, (int, float)) for item in value):
                    raise FilterValidationError(f"All items in range must be numbers")
                if value[0] > value[1]:
                    raise FilterValidationError(f"Range start must be less than or equal to range end")
            elif operator == 'in':
                if not isinstance(value, (list, tuple, set)):
                    raise FilterValidationError(f"Invalid value for 'in' operator: {value}")
                if not all(isinstance(item, (int, float)) for item in value):
                    raise FilterValidationError(f"All items in 'in' list must be numbers")
        
        # Handle date field types
        elif field_type in {'date', 'datetime'}:
            if operator in {'exact', 'gt', 'gte', 'lt', 'lte'}:
                if not isinstance(value, (date, datetime)):
                    raise FilterValidationError(f"Invalid value for date operator: {value}")
            elif operator == 'range':
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    raise FilterValidationError(f"Invalid value for range operator: {value}")
                if not all(isinstance(item, (date, datetime)) for item in value):
                    raise FilterValidationError(f"All items in range must be dates")
                if value[0] > value[1]:
                    raise FilterValidationError(f"Range start must be less than or equal to range end")
            elif operator in {'year', 'month', 'day', 'week_day'}:
                if not isinstance(value, int):
                    raise FilterValidationError(f"Invalid value for {operator} operator: {value}")
                if operator == 'year' and (value < 1900 or value > 2100):
                    raise FilterValidationError(f"Invalid year value: {value}")
                if operator == 'month' and (value < 1 or value > 12):
                    raise FilterValidationError(f"Invalid month value: {value}")
                if operator == 'day' and (value < 1 or value > 31):
                    raise FilterValidationError(f"Invalid day value: {value}")
                if operator == 'week_day' and (value < 1 or value > 7):
                    raise FilterValidationError(f"Invalid week_day value: {value}")
        
        # Handle time field type
        elif field_type == 'time':
            if operator in {'exact', 'gt', 'gte', 'lt', 'lte'}:
                if not isinstance(value, time):
                    raise FilterValidationError(f"Invalid value for time operator: {value}")
            elif operator in {'hour', 'minute', 'second'}:
                if not isinstance(value, int):
                    raise FilterValidationError(f"Invalid value for {operator} operator: {value}")
                if operator == 'hour' and (value < 0 or value > 23):
                    raise FilterValidationError(f"Invalid hour value: {value}")
                if operator == 'minute' and (value < 0 or value > 59):
                    raise FilterValidationError(f"Invalid minute value: {value}")
                if operator == 'second' and (value < 0 or value > 59):
                    raise FilterValidationError(f"Invalid second value: {value}")
        
        # Handle boolean field type
        elif field_type == 'boolean':
            if operator == 'exact':
                if not isinstance(value, bool):
                    raise FilterValidationError(f"Invalid value for boolean operator: {value}")
        
        # Handle choice field type
        elif field_type == 'choice':
            if operator == 'exact':
                # We can't validate against choices here as they're not provided
                # This would be validated at a higher level
                pass
            elif operator == 'in':
                if not isinstance(value, (list, tuple, set)):
                    raise FilterValidationError(f"Invalid value for 'in' operator: {value}")
        
        # Handle related field type
        elif field_type == 'related':
            if operator in {'exact', 'in'}:
                # We can't validate against related objects here as they're not provided
                # This would be validated at a higher level
                pass
        
        return True

class FilterValidator:
    """
    Validates filter data.
    """
    def __init__(self):
        self.field_type_validator = FieldTypeValidator()
        self.operator_validator = OperatorValidator()
        self.value_validator = ValueValidator()
        self.required_fields = {'field', 'type', 'operator', 'value'}
    
    def validate(self, filter_data: Dict[str, Any]) -> bool:
        """
        Validate filter data.
        
        Args:
            filter_data: The filter data to validate
            
        Returns:
            True if the filter data is valid
            
        Raises:
            FilterValidationError: If the filter data is not valid
        """
        # Check for required fields
        missing_fields = self.required_fields - set(filter_data.keys())
        if missing_fields:
            raise FilterValidationError(f"Missing required field(s): {', '.join(missing_fields)}")
        
        # Validate field type
        self.field_type_validator.validate(filter_data['field'], filter_data['type'])
        
        # Validate operator
        self.operator_validator.validate(filter_data['type'], filter_data['operator'])
        
        # Validate value
        self.value_validator.validate(filter_data['type'], filter_data['operator'], filter_data['value'])
        
        return True 