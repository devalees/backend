from django.db import models
from django.db.models import Q, QuerySet, Sum, Avg, Min, Max, Count
from typing import Dict, Any, List, Optional, Union, Callable
from .base import BaseFilterableModel, BaseAggregatableModel
from .registry import model_registry, ModelRegistry
from .aggregations import get_aggregation
from .caching import FilterCacheManager, AggregationCacheManager, CacheInvalidator

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
    
    # Cache manager for filter results
    _cache_invalidator = CacheInvalidator()
    _filter_cache_manager = FilterCacheManager(_cache_invalidator)
    
    @classmethod
    def get_filterable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of filterable fields and their types.
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
        """
        # Check if we have a cached result
        cached_result = cls._filter_cache_manager.get_cached_filter_result(cls, filters)
        if cached_result is not None:
            # Convert cached result back to queryset
            if isinstance(cached_result, list):
                ids = [item['id'] for item in cached_result if 'id' in item]
                if ids:
                    return cls.objects.filter(id__in=ids)
            return cls.objects.none()
        
        # If no cached result, apply filters
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
                    field_conditions |= Q(**{lookup: op_value})
                conditions &= field_conditions
            else:
                # Handle simple equality filter
                if field_type in ['char', 'text', 'email', 'url']:
                    conditions &= Q(**{f"{field}__icontains": value})
                else:
                    conditions &= Q(**{field: value})
        
        # Apply filters to queryset
        queryset = cls.objects.filter(conditions)
        
        # Cache the result
        result_list = list(queryset.values())
        cls._filter_cache_manager.cache_filter_result(cls, filters, result_list)
        
        return queryset
    
    @classmethod
    def invalidate_filter_cache(cls, filters=None):
        """
        Invalidate filter cache for this model.
        """
        if filters is not None:
            cls._filter_cache_manager.invalidate_filter_cache(cls, filters)
        else:
            cls._filter_cache_manager.invalidate_model_filter_cache(cls)

class AggregatableMixin:
    """
    Mixin that provides aggregation capabilities to a model.
    """
    
    # Cache manager for aggregation results
    _cache_invalidator = CacheInvalidator()
    _aggregation_cache_manager = AggregationCacheManager(_cache_invalidator)
    
    @classmethod
    def get_aggregatable_fields(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get the fields that can be aggregated.
        """
        fields = {}
        for field in cls._meta.fields:
            if isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                fields[field.name] = {
                    'type': field.get_internal_type(),
                    'field': field
                }
        return fields
    
    @classmethod
    def aggregate(cls, aggregations: Dict[str, Union[str, List[str]]], group_by: Optional[List[str]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Apply aggregations to the model.
        """
        # Check if we have a cached result
        cached_result = cls._aggregation_cache_manager.get_cached_aggregation_result(
            cls, aggregations, group_by
        )
        if cached_result is not None:
            return cached_result
        
        # If no cached result, apply aggregations
        aggregatable_fields = cls.get_aggregatable_fields()
        queryset = cls.objects
        
        # Validate fields and build annotations
        annotations = {}
        for field, agg_type in aggregations.items():
            if field not in aggregatable_fields:
                raise ValueError(f"Field '{field}' is not aggregatable")
            
            if isinstance(agg_type, list):
                for agg in agg_type:
                    agg_func = get_aggregation(agg, field)  # Fixed: Added field parameter
                    annotations[f"{field}__{agg}"] = agg_func
            else:
                agg_func = get_aggregation(agg_type, field)  # Fixed: Added field parameter
                annotations[f"{field}__{agg_type}"] = agg_func
        
        # Apply group by if specified
        if group_by:
            # Validate group by fields
            for field in group_by:
                if field not in cls._meta.fields:
                    raise ValueError(f"Field '{field}' does not exist")
            
            # Apply annotations and group by
            result = list(queryset.values(*group_by).annotate(**annotations))
        else:
            # Apply aggregations without grouping
            result = queryset.aggregate(**annotations)
        
        # Cache the result
        cls._aggregation_cache_manager.cache_aggregation_result(
            cls, aggregations, group_by, result
        )
        
        return result
    
    @classmethod
    def invalidate_aggregation_cache(cls, aggregations=None, group_by=None):
        """
        Invalidate aggregation cache for this model.
        """
        if aggregations is not None:
            cls._aggregation_cache_manager.invalidate_aggregation_cache(
                cls, aggregations, group_by
            )
        else:
            cls._aggregation_cache_manager.invalidate_model_aggregation_cache(cls)

class ModelRegistryMixin:
    """
    Mixin that provides model registration capabilities.
    """
    
    _registry = ModelRegistry()
    
    @classmethod
    def register_model_class(cls):
        """Register the model class with the registry."""
        cls._registry.register_model(cls)
    
    def register_model(self):
        """Register the model instance with the registry."""
        self._registry.register_model_instance(self)
    
    @classmethod
    def get_model_field_types(cls, model=None) -> Dict[str, str]:
        """Get the field types for a model."""
        if model is None:
            model = cls
        
        field_types = {}
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
        
        for field in model._meta.fields:
            field_type = field.get_internal_type()
            field_types[field.name] = type_mapping.get(field_type, field_type.lower())
        return field_types
    
    @classmethod
    def get_model_relationships(cls, model=None) -> Dict[str, Dict[str, Any]]:
        """Get the relationships for a model."""
        if model is None:
            model = cls
        
        relationships = {}
        for field in model._meta.fields:
            if field.is_relation:
                relationships[field.name] = {
                    'type': field.get_internal_type(),
                    'to': field.related_model.__name__,
                    'field': field
                }
        return relationships
    
    @classmethod
    def auto_discover_models(cls, app_label: str) -> None:
        """Auto-discover models in an app."""
        cls._registry.auto_discover_models(app_label) 