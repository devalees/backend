from django.db import models
from django.db.models import Q
from typing import Dict, Any, Callable, Type, Union, Optional

class BasicFilterFactory:
    """
    Factory for creating basic filters.
    This factory creates simple filters for standard field types.
    """
    
    def create_filter(self, field: str, value: Any) -> Q:
        """
        Create a basic filter for a field.
        
        Args:
            field: The field name
            value: The filter value
            
        Returns:
            A Q object representing the filter
        """
        return Q(**{field: value})
    
    def __eq__(self, other):
        """Compare two BasicFilterFactory instances"""
        return isinstance(other, BasicFilterFactory)

class AdvancedFilterFactory:
    """
    Factory for creating advanced filters with operators.
    This factory creates filters with specific operators for more complex filtering.
    """
    
    def create_filter(self, field: str, value: Dict[str, Any]) -> Q:
        """
        Create an advanced filter for a field with operators.
        
        Args:
            field: The field name
            value: A dictionary of operators and their values
            
        Returns:
            A Q object representing the filter
        """
        conditions = Q()
        for operator, op_value in value.items():
            lookup = f"{field}__{operator}"
            conditions &= Q(**{lookup: op_value})
        return conditions
    
    def __eq__(self, other):
        """Compare two AdvancedFilterFactory instances"""
        return isinstance(other, AdvancedFilterFactory)

class FilterTypeMapping:
    """
    Maps field types to filter factories.
    This class determines which filter factory to use based on the field type.
    """
    
    def __init__(self):
        self.basic_factory = BasicFilterFactory()
        self.advanced_factory = AdvancedFilterFactory()
        self.type_mapping = {
            'char': self.basic_factory,
            'text': self.basic_factory,
            'integer': self.basic_factory,
            'decimal': self.basic_factory,
            'float': self.basic_factory,
            'boolean': self.basic_factory,
            'datetime': self.basic_factory,
            'date': self.basic_factory,
            'time': self.basic_factory,
            'email': self.basic_factory,
            'url': self.basic_factory,
            'uuid': self.basic_factory,
            'json': self.basic_factory,
            'advanced': self.advanced_factory,
        }
    
    def get_filter_factory(self, field_type: str) -> Union[BasicFilterFactory, AdvancedFilterFactory]:
        """
        Get the appropriate filter factory for a field type.
        
        Args:
            field_type: The field type
            
        Returns:
            The appropriate filter factory
            
        Raises:
            ValueError: If the field type is not supported
        """
        if field_type not in self.type_mapping:
            raise ValueError(f"Unsupported field type: {field_type}")
        return self.type_mapping[field_type]

class FilterFactory:
    """
    Main factory for creating filters.
    This factory determines the appropriate filter factory to use based on the field type.
    """
    
    def __init__(self):
        self.type_mapping = FilterTypeMapping()
        self.custom_filters: Dict[str, Callable] = {}
        # Define valid operators for different field types
        self.valid_operators = {
            'char': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'],
            'text': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'],
            'integer': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range'],
            'decimal': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range'],
            'float': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range'],
            'boolean': ['exact'],
            'datetime': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range', 'year', 'month', 'day', 'week_day', 'hour', 'minute', 'second'],
            'date': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range', 'year', 'month', 'day', 'week_day'],
            'time': ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'range', 'hour', 'minute', 'second'],
            'email': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'],
            'url': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'],
            'uuid': ['exact', 'in'],
            'json': ['exact', 'contains', 'has_key', 'has_keys', 'has_any_keys'],
        }
    
    def create_filter_for_field(self, model: Type[models.Model], field: str, value: Any) -> Q:
        """
        Create a filter for a model field.
        
        Args:
            model: The model class
            field: The field name
            value: The filter value
            
        Returns:
            A Q object representing the filter
            
        Raises:
            ValueError: If the field is not filterable or the value is invalid
        """
        # Get filterable fields
        if hasattr(model, 'get_filterable_fields'):
            filterable_fields = model.get_filterable_fields()
        else:
            raise ValueError(f"Model {model.__name__} does not support filtering")
        
        # Check if field is filterable
        if field not in filterable_fields:
            raise ValueError(f"Field '{field}' is not filterable")
        
        # Get field type
        field_info = filterable_fields[field]
        field_type = field_info['type']
        
        # Check if value is a dictionary (advanced filter)
        if isinstance(value, dict):
            # Check if any of the operators are custom filters
            for operator in value.keys():
                if operator in self.custom_filters:
                    return self.custom_filters[operator](field, value[operator])
            
            # Validate operators
            for operator in value.keys():
                if field_type in self.valid_operators and operator not in self.valid_operators[field_type]:
                    raise ValueError(f"Invalid operator '{operator}' for field type '{field_type}'")
            
            # Use advanced filter factory
            factory = self.type_mapping.get_filter_factory('advanced')
            return factory.create_filter(field, value)
        else:
            # Use basic filter factory
            factory = self.type_mapping.get_filter_factory(field_type)
            return factory.create_filter(field, value)
    
    def register_custom_filter(self, name: str, filter_func: Callable) -> None:
        """
        Register a custom filter function.
        
        Args:
            name: The name of the custom filter
            filter_func: The function that implements the filter logic
        """
        if not callable(filter_func):
            raise ValueError("filter_func must be callable")
        self.custom_filters[name] = filter_func 