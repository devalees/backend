from django.db import models
from django.db.models import Q
from typing import Any, Dict, List, Union, Callable
from datetime import datetime, date, time
import re

class BaseFilter:
    """
    Base class for all filter types.
    Provides common functionality and interface for all filter implementations.
    """
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def apply(self, value: Any) -> Q:
        """
        Apply the filter to the given value.
        
        Args:
            value: The value to filter by
            
        Returns:
            Q object representing the filter condition
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is appropriate for this filter type.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")


class TextFilter(BaseFilter):
    """
    Filter for text fields.
    Supports various text matching operations.
    """
    def apply(self, value: Any) -> Q:
        """
        Apply text filter with case-insensitive contains by default.
        
        Args:
            value: The text value to filter by
            
        Returns:
            Q object for case-insensitive contains match
        """
        return Q(**{f"{self.field_name}__icontains": value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is a string.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is a string, False otherwise
        """
        return isinstance(value, str)


class NumericFilter(BaseFilter):
    """
    Filter for numeric fields.
    Supports comparison operations.
    """
    def apply(self, value: Any) -> Q:
        """
        Apply numeric filter with exact match by default.
        
        Args:
            value: The numeric value to filter by
            
        Returns:
            Q object for exact match
        """
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is a number.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is a number, False otherwise
        """
        return isinstance(value, (int, float))


class DateFilter(BaseFilter):
    """
    Filter for date fields.
    Supports date comparison operations.
    """
    def apply(self, value: Any) -> Q:
        """
        Apply date filter with exact match by default.
        
        Args:
            value: The date value to filter by
            
        Returns:
            Q object for exact match
        """
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is a date.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is a date, False otherwise
        """
        return isinstance(value, (date, datetime))


class TimeFilter(BaseFilter):
    """
    Filter for time fields.
    Supports time comparison operations.
    """
    def apply(self, value: Any) -> Q:
        """
        Apply time filter with exact match by default.
        
        Args:
            value: The time value to filter by
            
        Returns:
            Q object for exact match
        """
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is a time.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is a time, False otherwise
        """
        return isinstance(value, time)


class BooleanFilter(BaseFilter):
    """
    Filter for boolean fields.
    Supports true/false matching.
    """
    def apply(self, value: Any) -> Q:
        """
        Apply boolean filter with exact match.
        
        Args:
            value: The boolean value to filter by
            
        Returns:
            Q object for exact match
        """
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is a boolean.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is a boolean, False otherwise
        """
        return isinstance(value, bool)


class ChoiceFilter(BaseFilter):
    """
    Filter for choice fields.
    Supports exact matching against a set of choices.
    """
    def __init__(self, field_name: str, choices: List[Any]):
        super().__init__(field_name)
        self.choices = choices
    
    def apply(self, value: Any) -> Q:
        """
        Apply choice filter with exact match.
        
        Args:
            value: The choice value to filter by
            
        Returns:
            Q object for exact match
        """
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is in the list of choices.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is in the choices, False otherwise
        """
        return value in self.choices


class RelatedObjectFilter(BaseFilter):
    """
    Filter for related object fields.
    Supports filtering by related object attributes.
    """
    def __init__(self, field_name: str, related_field: str = None):
        super().__init__(field_name)
        self.related_field = related_field
    
    def apply(self, value: Any) -> Q:
        """
        Apply related object filter.
        
        Args:
            value: The value to filter by
            
        Returns:
            Q object for related object match
        """
        if self.related_field:
            return Q(**{f"{self.field_name}__{self.related_field}": value})
        return Q(**{self.field_name: value})
    
    def validate(self, value: Any) -> bool:
        """
        Validate that the value is appropriate for the related field.
        
        Args:
            value: The value to validate
            
        Returns:
            True if the value is valid, False otherwise
        """
        # For simplicity, we'll just check if the value is not None
        # In a real implementation, you might want to check against the related model's field type
        return value is not None


class FilterFactory:
    """
    Factory for creating filter instances based on field type.
    """
    @staticmethod
    def create_filter(field_name: str, field_type: str, **kwargs) -> BaseFilter:
        """
        Create a filter instance based on the field type.
        
        Args:
            field_name: The name of the field to filter on
            field_type: The type of the field
            **kwargs: Additional arguments for specific filter types
            
        Returns:
            A filter instance appropriate for the field type
            
        Raises:
            ValueError: If the field type is not supported
        """
        type_mapping = {
            'char': TextFilter,
            'text': TextFilter,
            'email': TextFilter,
            'url': TextFilter,
            'integer': NumericFilter,
            'decimal': NumericFilter,
            'float': NumericFilter,
            'boolean': BooleanFilter,
            'datetime': DateFilter,
            'date': DateFilter,
            'time': TimeFilter,
            'choice': ChoiceFilter,
        }
        
        filter_class = type_mapping.get(field_type)
        if not filter_class:
            raise ValueError(f"Unsupported field type: {field_type}")
        
        return filter_class(field_name, **kwargs)

def apply_filters(queryset, filter_json_str):
    """
    Apply filters to a queryset based on JSON-formatted filter criteria.
    
    Args:
        queryset: The Django queryset to filter
        filter_json_str: JSON string containing filter criteria
        
    Returns:
        Filtered queryset
    """
    import json
    
    # If empty, return unmodified queryset
    if not filter_json_str:
        return queryset
    
    try:
        # Parse the JSON filter criteria
        if isinstance(filter_json_str, str):
            filter_criteria = json.loads(filter_json_str)
        else:
            # Already a dict
            filter_criteria = filter_json_str
    except json.JSONDecodeError:
        # If invalid JSON, return unmodified queryset
        return queryset
    
    # Build query
    q_objects = Q()
    
    for field_name, value in filter_criteria.items():
        if "__" in field_name:
            # Handle lookups like field__contains, field__gt, etc.
            q_objects &= Q(**{field_name: value})
        else:
            # Default to exact match
            q_objects &= Q(**{field_name: value})
    
    return queryset.filter(q_objects)

def get_available_filters(model_class):
    """
    Get the available filters for a model class based on its FilterConfig.
    
    Args:
        model_class: The Django model class
        
    Returns:
        Dictionary of available filters by category
    """
    result = {
        'text': [],
        'number': [],
        'date': [],
        'boolean': [],
        'related': {},
        'lookups': [
            'exact', 'iexact', 'contains', 'icontains', 
            'gt', 'gte', 'lt', 'lte', 'in', 'startswith', 
            'istartswith', 'endswith', 'iendswith'
        ]
    }
    
    # Check if the model has a FilterConfig
    if hasattr(model_class, 'FilterConfig'):
        filter_config = model_class.FilterConfig
        
        # Add configured text fields
        if hasattr(filter_config, 'text'):
            result['text'] = filter_config.text
        
        # Add configured number fields
        if hasattr(filter_config, 'number'):
            result['number'] = filter_config.number
        
        # Add configured date fields
        if hasattr(filter_config, 'date'):
            result['date'] = filter_config.date
        
        # Add configured boolean fields
        if hasattr(filter_config, 'boolean'):
            result['boolean'] = filter_config.boolean
        
        # Add configured related fields
        if hasattr(filter_config, 'related'):
            result['related'] = filter_config.related
    
    return result 