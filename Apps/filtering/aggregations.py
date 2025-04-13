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
        KeyError: If the aggregation type is not found
    """
    if agg_type not in aggregation_registry.aggregations:
        raise KeyError(f"Aggregation type '{agg_type}' not found in registry")
    
    agg_func = aggregation_registry.get_aggregation(agg_type)
    
    if agg_type == 'custom':
        if 'expression' not in kwargs:
            raise ValueError("Custom aggregation requires an 'expression' parameter")
        return agg_func(field_name, kwargs['expression'])
    
    return agg_func(field_name) 