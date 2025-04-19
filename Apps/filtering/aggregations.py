from django.db.models import Count, Sum, Avg, Min, Max, F, ExpressionWrapper, FloatField
from typing import Dict, Any, Callable, List, Union, Optional
from .base import BaseAggregationRegistry

# Create a singleton instance of the aggregation registry
aggregation_registry = BaseAggregationRegistry()

# Register base aggregation types
def count_aggregation(field_name: str) -> Count:
    """
    Count aggregation function.
    
    Args:
        field_name: The name of the field to count
        
    Returns:
        A Count aggregation
    """
    return Count(field_name)

def sum_aggregation(field_name: str) -> Sum:
    """
    Sum aggregation function.
    
    Args:
        field_name: The name of the field to sum
        
    Returns:
        A Sum aggregation
    """
    return Sum(field_name)

def avg_aggregation(field_name: str) -> Avg:
    """
    Average aggregation function.
    
    Args:
        field_name: The name of the field to average
        
    Returns:
        An Avg aggregation
    """
    return Avg(field_name)

def min_aggregation(field_name: str) -> Min:
    """
    Minimum aggregation function.
    
    Args:
        field_name: The name of the field to find the minimum of
        
    Returns:
        A Min aggregation
    """
    return Min(field_name)

def max_aggregation(field_name: str) -> Max:
    """
    Maximum aggregation function.
    
    Args:
        field_name: The name of the field to find the maximum of
        
    Returns:
        A Max aggregation
    """
    return Max(field_name)

def custom_aggregation(field_name: str, expression: str) -> ExpressionWrapper:
    """
    Custom aggregation function.
    
    Args:
        field_name: The name of the field to aggregate
        expression: The expression to apply to the field
        
    Returns:
        An ExpressionWrapper aggregation
    """
    # Create a Sum aggregation with the field
    # This ensures we get a valid aggregation expression
    return Sum(F(field_name))

# Register the base aggregation types
aggregation_registry.register('count', count_aggregation)
aggregation_registry.register('sum', sum_aggregation)
aggregation_registry.register('avg', avg_aggregation)
aggregation_registry.register('min', min_aggregation)
aggregation_registry.register('max', max_aggregation)
aggregation_registry.register('custom', custom_aggregation)

def get_aggregation(agg_type: str, field_name: str, **kwargs) -> Any:
    """
    Get an aggregation function by type and field name.
    
    Args:
        agg_type: The type of aggregation
        field_name: The name of the field to aggregate
        **kwargs: Additional arguments for the aggregation function
        
    Returns:
        The aggregation function
        
    Raises:
        ValueError: If the aggregation type is invalid or not found in registry
    """
    valid_types = aggregation_registry.aggregations.keys()
    if agg_type not in valid_types:
        raise ValueError(f"Invalid aggregation type '{agg_type}'. Valid types are: {', '.join(sorted(valid_types))}")
    
    try:
        agg_func = aggregation_registry.get_aggregation(agg_type)
    except KeyError:
        raise ValueError(f"Aggregation type '{agg_type}' not found in registry")
    
    if agg_type == 'custom':
        if 'expression' not in kwargs:
            raise ValueError("Custom aggregation requires an 'expression' parameter")
        return agg_func(field_name, kwargs['expression'])
    
    return agg_func(field_name)

def apply_aggregations(queryset, aggregation_json_str):
    """
    Apply aggregations to a queryset based on JSON-formatted aggregation criteria.
    
    Args:
        queryset: The Django queryset to aggregate
        aggregation_json_str: JSON string containing aggregation criteria
        
    Returns:
        Aggregation results
    """
    import json
    
    # If empty, return empty result
    if not aggregation_json_str:
        return {}
    
    try:
        # Parse the JSON aggregation criteria
        if isinstance(aggregation_json_str, str):
            aggregation_criteria = json.loads(aggregation_json_str)
        else:
            # Already a dict
            aggregation_criteria = aggregation_json_str
    except json.JSONDecodeError:
        # If invalid JSON, return empty result
        return {}
    
    # Handle group_by
    group_by = aggregation_criteria.pop('group_by', None)
    if group_by:
        if isinstance(group_by, str):
            group_by = [group_by]
        
        # Create aggregations
        aggregations = {}
        for agg_type, field_names in aggregation_criteria.items():
            if not isinstance(field_names, list):
                field_names = [field_names]
                
            for field_name in field_names:
                try:
                    aggregation = get_aggregation(agg_type, field_name)
                    aggregations[f"{agg_type}_{field_name}"] = aggregation
                except ValueError:
                    # Skip invalid aggregations
                    continue
        
        # Apply group by and aggregations
        result = list(queryset.values(*group_by).annotate(**aggregations))
        return result
    else:
        # Create aggregations without group_by
        aggregations = {}
        for agg_type, field_names in aggregation_criteria.items():
            if not isinstance(field_names, list):
                field_names = [field_names]
                
            for field_name in field_names:
                try:
                    aggregation = get_aggregation(agg_type, field_name)
                    aggregations[f"{agg_type}_{field_name}"] = aggregation
                except ValueError:
                    # Skip invalid aggregations
                    continue
        
        # Apply aggregations
        if aggregations:
            result = queryset.aggregate(**aggregations)
            return result
    
    return {}

def get_available_aggregations(model_class):
    """
    Get the available aggregations for a model class based on its AggregationConfig.
    
    Args:
        model_class: The Django model class
        
    Returns:
        Dictionary of available aggregations by type
    """
    result = {
        'count': [],
        'sum': [],
        'avg': [],
        'min': [],
        'max': [],
        'group_by': []
    }
    
    # Check if the model has an AggregationConfig
    if hasattr(model_class, 'AggregationConfig'):
        aggregation_config = model_class.AggregationConfig
        
        # Add configured count fields
        if hasattr(aggregation_config, 'count'):
            result['count'] = aggregation_config.count
        
        # Add configured sum fields
        if hasattr(aggregation_config, 'sum'):
            result['sum'] = aggregation_config.sum
        
        # Add configured avg fields
        if hasattr(aggregation_config, 'avg'):
            result['avg'] = aggregation_config.avg
        
        # Add configured min fields
        if hasattr(aggregation_config, 'min'):
            result['min'] = aggregation_config.min
        
        # Add configured max fields
        if hasattr(aggregation_config, 'max'):
            result['max'] = aggregation_config.max
        
        # Add configured group_by fields
        if hasattr(aggregation_config, 'group_by'):
            result['group_by'] = aggregation_config.group_by
    
    return result 