from django.db import models
from django.db.models import Q, QuerySet, Sum, Avg, Min, Max, Count
from typing import Dict, Any, List, Optional, Union, Callable
from .base import BaseFilterableModel, BaseAggregatableModel
from .registry import model_registry, ModelRegistry
from .aggregations import get_aggregation

class FilterableMixin:
    """
    Mixin that provides filtering capabilities to a model.
    This mixin can be used with any Django model to add filtering functionality.
    """
    
    # Valid filter operators for fields
    FILTER_OPERATORS = {
        'exact': 'Exact match',
        'iexact': 'Case-insensitive exact match',
        'contains': 'Contains substring',
        'icontains': 'Case-insensitive contains',
        'in': 'In a list of values',
        'gt': 'Greater than',
        'gte': 'Greater than or equal',
        'lt': 'Less than',
        'lte': 'Less than or equal',
        'startswith': 'Starts with',
        'istartswith': 'Case-insensitive starts with',
        'endswith': 'Ends with',
        'iendswith': 'Case-insensitive ends with',
        'regex': 'Regular expression match',
        'iregex': 'Case-insensitive regex',
        'isnull': 'Is null',
        'range': 'Range of values',
    }
    
    @classmethod
    def get_filterable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of filterable fields and their types.
        This method is similar to BaseFilterableModel.get_filterable_fields but works as a mixin.
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
    
    @classmethod
    def filter(cls, filters):
        """
        Filter queryset based on provided filters.
        
        Args:
            filters (dict): A dictionary of field names and their filter conditions.
                          Each field can have multiple operators as a nested dictionary.
                          Example: {'name': {'startswith': 'Test', 'contains': 'Model'}}
                          For string fields, a simple value will use icontains by default.
        
        Returns:
            QuerySet: Filtered queryset
        
        Raises:
            ValueError: If field is not filterable or operator is invalid
        """
        conditions = Q()
        filterable_fields = cls.get_filterable_fields()
        
        for field, value in filters.items():
            if field not in filterable_fields:
                raise ValueError(f"Field '{field}' is not filterable")
            
            field_info = filterable_fields[field]
            field_type = field_info['type']
            
            if isinstance(value, dict):
                # Handle complex filters with operators
                field_conditions = Q()
                for operator, op_value in value.items():
                    if operator not in cls.FILTER_OPERATORS:
                        raise ValueError(f"Invalid operator '{operator}'")
                    
                    lookup = f"{field}__{operator}"
                    field_conditions |= Q(**{lookup: op_value})  # OR between operators
                conditions &= field_conditions  # AND between fields
            else:
                # Handle simple equality filter
                if field_type in ['char', 'text', 'email', 'url']:
                    # Use icontains for string fields by default
                    conditions &= Q(**{f"{field}__icontains": value})
                else:
                    # Use exact match for non-string fields
                    conditions &= Q(**{field: value})
        
        return cls.objects.filter(conditions)

class AggregatableMixin:
    """
    Mixin that provides aggregation capabilities to a model.
    This mixin can be used with any Django model to add aggregation functionality.
    """
    
    @classmethod
    def get_aggregatable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of aggregatable fields and their types.
        This method is similar to BaseAggregatableModel.get_aggregatable_fields but works as a mixin.
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
    
    @classmethod
    def aggregate(cls, aggregations: Dict[str, Union[str, List[str]]], group_by: Optional[List[str]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Apply aggregations to the model's queryset.
        
        Args:
            aggregations: A dictionary of field names and aggregation types
            group_by: Optional list of fields to group by
            
        Returns:
            A dictionary of aggregation results or a list of dictionaries if grouped
            
        Raises:
            ValueError: If an invalid field or aggregation type is provided
        """
        # Get aggregatable fields
        aggregatable_fields = cls.get_aggregatable_fields()
        
        # Initialize queryset
        queryset = cls.objects.all()
        
        # Handle group by
        if group_by:
            # Validate group by fields against model fields
            for field in group_by:
                if not hasattr(cls, field) and field not in cls._meta.fields:
                    raise ValueError(f"Field '{field}' does not exist")
            
            # Apply group by
            queryset = queryset.values(*group_by)
        
        # Apply aggregations
        agg_dict = {}
        
        for field_name, agg_types in aggregations.items():
            # Check if field is aggregatable
            if field_name not in aggregatable_fields and field_name != 'id':
                raise ValueError(f"Field '{field_name}' is not aggregatable")
            
            # Handle single aggregation type
            if isinstance(agg_types, str):
                agg_types = [agg_types]
            
            # Apply each aggregation type
            for agg_type in agg_types:
                try:
                    # Use the new get_aggregation function
                    agg_dict[f"{field_name}__{agg_type}"] = get_aggregation(agg_type, field_name)
                except (KeyError, ValueError) as e:
                    raise ValueError(f"Invalid aggregation type '{agg_type}' for field '{field_name}': {str(e)}")
        
        # Apply aggregations differently based on whether we're grouping
        if group_by:
            # For grouped results, use annotate() and return list
            result = queryset.annotate(**agg_dict)
            return list(result)
        else:
            # For non-grouped results, use aggregate() and return dict
            return queryset.aggregate(**agg_dict)

class ModelRegistryMixin:
    """
    Mixin that provides model registration capabilities.
    This mixin can be used with any Django model to add registration functionality.
    """
    
    _registry = ModelRegistry()
    
    @classmethod
    def register_model_class(cls):
        """Register the model class with the registry."""
        cls._registry.register_model(cls)
    
    def register_model(self):
        """Register this model instance's class with the registry."""
        self.__class__.register_model_class()
    
    @classmethod
    def get_model_field_types(cls, model=None) -> Dict[str, str]:
        """
        Get the field types for a model.
        
        Args:
            model: Optional model class. If not provided, uses the current class.
            
        Returns:
            Dictionary of field names and their types
        """
        model = model or cls
        return model._registry.get_model_field_types(model)
    
    @classmethod
    def get_model_relationships(cls, model=None) -> Dict[str, Dict[str, Any]]:
        """
        Get the relationships for a model.
        
        Args:
            model: Optional model class. If not provided, uses the current class.
            
        Returns:
            Dictionary of relationship names and their details
        """
        model = model or cls
        return model._registry.get_model_relationships(model)
    
    @classmethod
    def auto_discover_models(cls, app_label: str) -> None:
        """
        Automatically discover and register models from a Django app.
        
        Args:
            app_label: The label of the Django app to discover models from
        """
        cls._registry.auto_discover_models(app_label) 