from django.db.models import Count, Sum, Avg, Min, Max, F, ExpressionWrapper, FloatField
from django.db.models.query import QuerySet
from typing import Dict, Any, List, Union, Tuple, Optional
from .aggregations import get_aggregation, aggregation_registry

def create_group_by_aggregation(fields: Union[str, List[str]], queryset: Optional[QuerySet] = None) -> Dict[str, Any]:
    """
    Create a group by aggregation for the specified fields.
    
    Args:
        fields: A single field name or a list of field names to group by
        queryset: Optional queryset to validate field names against
        
    Returns:
        A dictionary containing the group by fields
        
    Raises:
        ValueError: If the fields parameter is empty or invalid
    """
    if not fields:
        raise ValueError("Fields parameter cannot be empty")
    
    # Convert a single field to a list
    if isinstance(fields, str):
        fields = [fields]
    
    # Validate that all fields are strings
    if not all(isinstance(field, str) for field in fields):
        raise ValueError("All fields must be strings")
    
    # Validate field names against model fields if queryset is provided
    if queryset is not None:
        model_fields = [f.name for f in queryset.model._meta.get_fields()]
        invalid_fields = [field for field in fields if field not in model_fields]
        if invalid_fields:
            raise ValueError(f"Invalid field names: {', '.join(invalid_fields)}")
    
    return {
        'group_by_fields': fields
    }

def create_multiple_aggregations(aggregations: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Create multiple aggregations for the specified fields.
    
    Args:
        aggregations: A list of tuples containing (aggregation_type, field_name)
        
    Returns:
        A dictionary containing the multiple aggregations
        
    Raises:
        ValueError: If the aggregations parameter is empty or invalid
    """
    if not aggregations:
        raise ValueError("Aggregations parameter cannot be empty")
    
    # Validate that all aggregations are tuples with two elements
    if not all(isinstance(agg, tuple) and len(agg) == 2 for agg in aggregations):
        raise ValueError("All aggregations must be tuples with two elements")
    
    # Validate that all aggregation types are valid
    for agg_type, _ in aggregations:
        if agg_type not in aggregation_registry.aggregations:
            raise ValueError(f"Invalid aggregation type: {agg_type}")
    
    return {
        'multiple_aggregations': aggregations
    }

def create_nested_aggregations(aggregations: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Create nested aggregations for the specified fields.
    
    Args:
        aggregations: A list of tuples containing (aggregation_type, field_name)
        
    Returns:
        A dictionary containing the nested aggregations
        
    Raises:
        ValueError: If the aggregations parameter is empty or invalid
    """
    if not aggregations:
        raise ValueError("Aggregations parameter cannot be empty")
    
    # Validate that all aggregations are tuples with two elements
    if not all(isinstance(agg, tuple) and len(agg) == 2 for agg in aggregations):
        raise ValueError("All aggregations must be tuples with two elements")
    
    # Validate that all aggregation types are valid
    for agg_type, _ in aggregations:
        if agg_type not in aggregation_registry.aggregations:
            raise ValueError(f"Invalid aggregation type: {agg_type}")
    
    return {
        'nested_aggregations': aggregations
    }

def apply_group_by_aggregations(
    queryset: QuerySet,
    group_by_agg: Dict[str, Any],
    multiple_agg: Optional[Dict[str, Any]] = None,
    nested_agg: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Apply group by aggregations to a queryset.
    
    Args:
        queryset: The queryset to apply the aggregations to
        group_by_agg: The group by aggregation
        multiple_agg: Optional multiple aggregations
        nested_agg: Optional nested aggregations
        
    Returns:
        A list of dictionaries containing the grouped and aggregated data
    """
    # Get the group by fields
    group_by_fields = group_by_agg['group_by_fields']
    
    # Create the annotations dictionary
    annotations = {}
    
    # Add count annotation
    annotations['count'] = Count('id')
    
    # Add multiple aggregations if provided
    if multiple_agg and 'multiple_aggregations' in multiple_agg:
        for agg_type, field_name in multiple_agg['multiple_aggregations']:
            # Get the aggregation function
            agg_func = get_aggregation(agg_type, field_name)
            
            # Add the aggregation to the annotations
            annotations[f'{field_name}_{agg_type}'] = agg_func
    
    # Add nested aggregations if provided
    if nested_agg and 'nested_aggregations' in nested_agg:
        for agg_type, field_name in nested_agg['nested_aggregations']:
            # Get the aggregation function
            agg_func = get_aggregation(agg_type, field_name)
            
            # Add the aggregation to the annotations
            annotations[f'{field_name}_{agg_type}'] = agg_func
    
    # Apply the group by and annotations
    result = queryset.values(*group_by_fields).annotate(**annotations)
    
    # Convert the result to a list of dictionaries
    return list(result) 