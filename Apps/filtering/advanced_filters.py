from django.db import models
from django.db.models import Q
from typing import Any, Dict, List, Union, Callable, Optional
from datetime import datetime, date, time
import re
from .filters import BaseFilter, TextFilter, NumericFilter, DateFilter, TimeFilter, BooleanFilter, ChoiceFilter, RelatedObjectFilter

class AdvancedTextFilter(TextFilter):
    """
    Advanced text filter with support for various text matching operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'iexact': lambda field, value: Q(**{f"{field}__iexact": value}),
        'contains': lambda field, value: Q(**{f"{field}__contains": value}),
        'icontains': lambda field, value: Q(**{f"{field}__icontains": value}),
        'startswith': lambda field, value: Q(**{f"{field}__startswith": value}),
        'istartswith': lambda field, value: Q(**{f"{field}__istartswith": value}),
        'endswith': lambda field, value: Q(**{f"{field}__endswith": value}),
        'iendswith': lambda field, value: Q(**{f"{field}__iendswith": value}),
        'regex': lambda field, value: Q(**{f"{field}__regex": value}),
        'iregex': lambda field, value: Q(**{f"{field}__iregex": value}),
    }
    
    def __init__(self, field_name: str, operator: str = 'icontains'):
        super().__init__(field_name)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for TextFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply text filter with the specified operator.
        
        Args:
            value: The text value to filter by
            
        Returns:
            Q object for the specified text matching operation
        """
        if not self.validate(value):
            raise ValueError(f"Invalid value '{value}' for TextFilter with operator '{self.operator}'")
            
        # Validate regex pattern if using regex operators
        if self.operator in ['regex', 'iregex']:
            try:
                re.compile(value)
            except re.error:
                raise ValueError(f"Invalid regex pattern '{value}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedNumericFilter(NumericFilter):
    """
    Advanced numeric filter with support for various comparison operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'gt': lambda field, value: Q(**{f"{field}__gt": value}),
        'gte': lambda field, value: Q(**{f"{field}__gte": value}),
        'lt': lambda field, value: Q(**{f"{field}__lt": value}),
        'lte': lambda field, value: Q(**{f"{field}__lte": value}),
        'in': lambda field, value: Q(**{f"{field}__in": value}),
        'range': lambda field, value: Q(**{f"{field}__range": value}),
    }
    
    def __init__(self, field_name: str, operator: str = 'exact'):
        super().__init__(field_name)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for NumericFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply numeric filter with the specified operator.
        
        Args:
            value: The numeric value to filter by
            
        Returns:
            Q object for the specified numeric comparison operation
        """
        # Special handling for 'in' and 'range' operators which expect lists
        if self.operator == 'in':
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"Operator 'in' requires a list or tuple of values")
            # Validate each item in the list
            for item in value:
                if not isinstance(item, (int, float)):
                    raise ValueError(f"Invalid value '{item}' in list for NumericFilter with operator 'in'")
        elif self.operator == 'range':
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f"Operator 'range' requires a list or tuple with exactly 2 values")
            # Validate each item in the range
            for item in value:
                if not isinstance(item, (int, float)):
                    raise ValueError(f"Invalid value '{item}' in range for NumericFilter with operator 'range'")
        else:
            # For other operators, validate the single value
            if not self.validate(value):
                raise ValueError(f"Invalid value '{value}' for NumericFilter with operator '{self.operator}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedDateFilter(DateFilter):
    """
    Advanced date filter with support for various date comparison operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'gt': lambda field, value: Q(**{f"{field}__gt": value}),
        'gte': lambda field, value: Q(**{f"{field}__gte": value}),
        'lt': lambda field, value: Q(**{f"{field}__lt": value}),
        'lte': lambda field, value: Q(**{f"{field}__lte": value}),
        'year': lambda field, value: Q(**{f"{field}__year": value}),
        'month': lambda field, value: Q(**{f"{field}__month": value}),
        'day': lambda field, value: Q(**{f"{field}__day": value}),
        'week_day': lambda field, value: Q(**{f"{field}__week_day": value}),
        'range': lambda field, value: Q(**{f"{field}__range": value}),
    }
    
    def __init__(self, field_name: str, operator: str = 'exact'):
        super().__init__(field_name)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for DateFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply date filter with the specified operator.
        
        Args:
            value: The date value to filter by
            
        Returns:
            Q object for the specified date comparison operation
        """
        # Special handling for 'range' operator which expects a list of two dates
        if self.operator == 'range':
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f"Operator 'range' requires a list or tuple with exactly 2 date values")
            # Validate each date in the range
            for date_val in value:
                if not isinstance(date_val, (date, datetime)):
                    raise ValueError(f"Invalid value '{date_val}' in range for DateFilter with operator 'range'")
        # Special handling for year, month, day, week_day operators which expect integers
        elif self.operator in ['year', 'month', 'day', 'week_day']:
            if not isinstance(value, int):
                raise ValueError(f"Operator '{self.operator}' requires an integer value")
            # Validate date component ranges
            if self.operator == 'month' and (value < 1 or value > 12):
                raise ValueError(f"Invalid month value: {value}. Must be between 1 and 12")
            elif self.operator == 'day' and (value < 1 or value > 31):
                raise ValueError(f"Invalid day value: {value}. Must be between 1 and 31")
            elif self.operator == 'week_day' and (value < 1 or value > 7):
                raise ValueError(f"Invalid week day value: {value}. Must be between 1 and 7")
        else:
            # For other operators, validate the date value
            if not self.validate(value):
                raise ValueError(f"Invalid value '{value}' for DateFilter with operator '{self.operator}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedTimeFilter(TimeFilter):
    """
    Advanced time filter with support for various time comparison operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'gt': lambda field, value: Q(**{f"{field}__gt": value}),
        'gte': lambda field, value: Q(**{f"{field}__gte": value}),
        'lt': lambda field, value: Q(**{f"{field}__lt": value}),
        'lte': lambda field, value: Q(**{f"{field}__lte": value}),
        'hour': lambda field, value: Q(**{f"{field}__hour": value}),
        'minute': lambda field, value: Q(**{f"{field}__minute": value}),
        'second': lambda field, value: Q(**{f"{field}__second": value}),
        'range': lambda field, value: Q(**{f"{field}__range": value}),
    }
    
    def __init__(self, field_name: str, operator: str = 'exact'):
        super().__init__(field_name)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for TimeFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply time filter with the specified operator.
        
        Args:
            value: The time value to filter by
            
        Returns:
            Q object for the specified time comparison operation
        """
        # Special handling for 'range' operator which expects a list of two times
        if self.operator == 'range':
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f"Operator 'range' requires a list or tuple with exactly 2 time values")
            # Validate each time in the range
            for time_val in value:
                if not isinstance(time_val, time):
                    raise ValueError(f"Invalid value '{time_val}' in range for TimeFilter with operator 'range'")
        # Special handling for hour, minute, second operators which expect integers
        elif self.operator in ['hour', 'minute', 'second']:
            if not isinstance(value, int):
                raise ValueError(f"Operator '{self.operator}' requires an integer value")
            # Validate time component ranges
            if self.operator == 'hour' and (value < 0 or value > 23):
                raise ValueError(f"Invalid hour value: {value}. Must be between 0 and 23")
            elif self.operator == 'minute' and (value < 0 or value > 59):
                raise ValueError(f"Invalid minute value: {value}. Must be between 0 and 59")
            elif self.operator == 'second' and (value < 0 or value > 59):
                raise ValueError(f"Invalid second value: {value}. Must be between 0 and 59")
        else:
            # For other operators, validate the time value
            if not self.validate(value):
                raise ValueError(f"Invalid value '{value}' for TimeFilter with operator '{self.operator}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedBooleanFilter(BooleanFilter):
    """
    Advanced boolean filter with support for various boolean operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'isnull': lambda field, value: Q(**{f"{field}__isnull": value}),
    }
    
    def __init__(self, field_name: str, operator: str = 'exact'):
        super().__init__(field_name)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for BooleanFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply boolean filter with the specified operator.
        
        Args:
            value: The boolean value to filter by
            
        Returns:
            Q object for the specified boolean operation
        """
        if not self.validate(value):
            raise ValueError(f"Invalid value '{value}' for BooleanFilter with operator '{self.operator}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedChoiceFilter(ChoiceFilter):
    """
    Advanced choice filter with support for various choice operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'in': lambda field, value: Q(**{f"{field}__in": value}),
    }
    
    def __init__(self, field_name: str, choices: List[Any], operator: str = 'exact'):
        super().__init__(field_name, choices)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for ChoiceFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply choice filter with the specified operator.
        
        Args:
            value: The choice value to filter by
            
        Returns:
            Q object for the specified choice operation
        """
        # Special handling for 'in' operator which expects a list of choices
        if self.operator == 'in':
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"Operator 'in' requires a list or tuple of values")
            # Validate each choice in the list
            for choice in value:
                if choice not in self.choices:
                    raise ValueError(f"Invalid value '{choice}' in list for ChoiceFilter with operator 'in'")
        else:
            # For other operators, validate the single choice
            if not self.validate(value):
                raise ValueError(f"Invalid value '{value}' for ChoiceFilter with operator '{self.operator}'")
        
        return self.OPERATORS[self.operator](self.field_name, value)


class AdvancedRelatedObjectFilter(RelatedObjectFilter):
    """
    Advanced related object filter with support for various related object operations.
    """
    OPERATORS = {
        'exact': lambda field, value: Q(**{field: value}),
        'iexact': lambda field, value: Q(**{f"{field}__iexact": value}),
        'contains': lambda field, value: Q(**{f"{field}__contains": value}),
        'icontains': lambda field, value: Q(**{f"{field}__icontains": value}),
        'startswith': lambda field, value: Q(**{f"{field}__startswith": value}),
        'istartswith': lambda field, value: Q(**{f"{field}__istartswith": value}),
        'endswith': lambda field, value: Q(**{f"{field}__endswith": value}),
        'iendswith': lambda field, value: Q(**{f"{field}__iendswith": value}),
        'in': lambda field, value: Q(**{f"{field}__in": value}),
        'isnull': lambda field, value: Q(**{f"{field}__isnull": value}),
    }
    
    def __init__(self, field_name: str, related_field: Optional[str] = None, operator: str = 'exact'):
        super().__init__(field_name, related_field)
        self.operator = operator
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator '{operator}' for RelatedObjectFilter")
    
    def apply(self, value: Any) -> Q:
        """
        Apply related object filter with the specified operator.
        
        Args:
            value: The value to filter by
            
        Returns:
            Q object for the specified related object operation
        """
        # Special handling for 'in' operator which expects a list
        if self.operator == 'in':
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"Operator 'in' requires a list or tuple of values")
            # Validate each value in the list
            for val in value:
                if not self.validate(val):
                    raise ValueError(f"Invalid value '{val}' in list for RelatedObjectFilter with operator 'in'")
        else:
            # For other operators, validate the single value
            if not self.validate(value):
                raise ValueError(f"Invalid value '{value}' for RelatedObjectFilter with operator '{self.operator}'")
        
        # Build the field path
        field_path = self.field_name
        if self.related_field:
            field_path = f"{field_path}__{self.related_field}"
        
        return self.OPERATORS[self.operator](field_path, value)


class AdvancedFilterFactory:
    """
    Factory for creating advanced filter instances based on field type.
    """
    @staticmethod
    def create_filter(field_name: str, field_type: str, operator: str = None, **kwargs) -> BaseFilter:
        """
        Create an advanced filter instance based on the field type.
        
        Args:
            field_name: The name of the field to filter on
            field_type: The type of the field
            operator: The operator to use for the filter
            **kwargs: Additional arguments for specific filter types
            
        Returns:
            An advanced filter instance appropriate for the field type
            
        Raises:
            ValueError: If the field type is not supported
        """
        type_mapping = {
            'char': (AdvancedTextFilter, 'icontains'),
            'text': (AdvancedTextFilter, 'icontains'),
            'email': (AdvancedTextFilter, 'iexact'),
            'url': (AdvancedTextFilter, 'iexact'),
            'integer': (AdvancedNumericFilter, 'exact'),
            'decimal': (AdvancedNumericFilter, 'exact'),
            'float': (AdvancedNumericFilter, 'exact'),
            'boolean': (AdvancedBooleanFilter, 'exact'),
            'datetime': (AdvancedDateFilter, 'exact'),
            'date': (AdvancedDateFilter, 'exact'),
            'time': (AdvancedTimeFilter, 'exact'),
            'choice': (AdvancedChoiceFilter, 'exact'),
        }
        
        filter_info = type_mapping.get(field_type)
        if not filter_info:
            raise ValueError(f"Unsupported field type: {field_type}")
        
        filter_class, default_operator = filter_info
        operator = operator or default_operator
        
        return filter_class(field_name, operator=operator, **kwargs) 