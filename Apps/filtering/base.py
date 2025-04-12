from django.db import models
from typing import Dict, Any, Callable, Type

class BaseFilterableModel(models.Model):
    """
    Abstract base model that provides filtering capabilities.
    Models inheriting from this class will automatically get filtering functionality.
    """
    class Meta:
        abstract = True

    @classmethod
    def get_filterable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of filterable fields and their types.
        Override this method to customize which fields are filterable.
        """
        fields = {}
        type_mapping = {
            'CharField': 'char',
            'TextField': 'text',
            'IntegerField': 'integer',
            'DecimalField': 'decimal',
            'FloatField': 'float',
            'BooleanField': 'boolean',
            'DateTimeField': 'datetime',
            'DateField': 'date',
            'TimeField': 'time',
            'EmailField': 'email',
            'URLField': 'url',
            'UUIDField': 'uuid',
            'JSONField': 'json',
        }
        
        for field in cls._meta.fields:
            field_type = field.get_internal_type()
            normalized_type = type_mapping.get(field_type, field_type.lower())
            fields[field.name] = {
                'type': normalized_type,
                'field': field
            }
        return fields

class BaseAggregatableModel(models.Model):
    """
    Abstract base model that provides aggregation capabilities.
    Models inheriting from this class will automatically get aggregation functionality.
    """
    class Meta:
        abstract = True

    @classmethod
    def get_aggregatable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of aggregatable fields and their types.
        Override this method to customize which fields are aggregatable.
        """
        fields = {}
        type_mapping = {
            'IntegerField': 'integer',
            'DecimalField': 'decimal',
            'FloatField': 'float',
        }
        
        for field in cls._meta.fields:
            if isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
                field_type = field.get_internal_type()
                normalized_type = type_mapping.get(field_type, field_type.lower())
                fields[field.name] = {
                    'type': normalized_type,
                    'field': field
                }
        return fields

class BaseFilterRegistry:
    """
    Registry for filter types that can be applied to models.
    This class manages the registration and retrieval of filter functions.
    """
    def __init__(self):
        self.filters: Dict[str, Callable] = {}

    def register(self, name: str, filter_func: Callable) -> None:
        """
        Register a new filter type.
        
        Args:
            name: The name of the filter type
            filter_func: The function that implements the filter logic
        """
        if not callable(filter_func):
            raise ValueError("filter_func must be callable")
        self.filters[name] = filter_func

    def get_filter(self, name: str) -> Callable:
        """
        Get a registered filter by name.
        
        Args:
            name: The name of the filter to retrieve
            
        Returns:
            The filter function
            
        Raises:
            KeyError: If the filter is not found
        """
        if name not in self.filters:
            raise KeyError(f"Filter '{name}' not found in registry")
        return self.filters[name]

class BaseAggregationRegistry:
    """
    Registry for aggregation types that can be applied to models.
    This class manages the registration and retrieval of aggregation functions.
    """
    def __init__(self):
        self.aggregations: Dict[str, Callable] = {}

    def register(self, name: str, aggregation_func: Callable) -> None:
        """
        Register a new aggregation type.
        
        Args:
            name: The name of the aggregation type
            aggregation_func: The function that implements the aggregation logic
        """
        if not callable(aggregation_func):
            raise ValueError("aggregation_func must be callable")
        self.aggregations[name] = aggregation_func

    def get_aggregation(self, name: str) -> Callable:
        """
        Get a registered aggregation by name.
        
        Args:
            name: The name of the aggregation to retrieve
            
        Returns:
            The aggregation function
            
        Raises:
            KeyError: If the aggregation is not found
        """
        if name not in self.aggregations:
            raise KeyError(f"Aggregation '{name}' not found in registry")
        return self.aggregations[name] 