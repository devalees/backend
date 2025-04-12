from django.db.models import Q
from typing import Dict, Any, List, Union, Optional, Type, Callable
from .filters import (
    BaseFilter, TextFilter, NumericFilter, DateFilter, 
    TimeFilter, BooleanFilter, ChoiceFilter, RelatedObjectFilter
)
from .advanced_filters import (
    AdvancedTextFilter, AdvancedNumericFilter, AdvancedDateFilter,
    AdvancedTimeFilter, AdvancedBooleanFilter, AdvancedChoiceFilter,
    AdvancedRelatedObjectFilter
)

class FilterCombination:
    """
    Base class for filter combinations.
    Provides common functionality for combining multiple filters.
    """
    def __init__(self, filters: List[BaseFilter]):
        """
        Initialize a filter combination with a list of filters.
        
        Args:
            filters: List of filter objects to combine
        """
        self.filters = filters
    
    def apply(self, values: Dict[str, Any]) -> Q:
        """
        Apply the filter combination to the given values.
        
        Args:
            values: Dictionary of field names and their values
            
        Returns:
            Q object representing the combined filter conditions
        """
        raise NotImplementedError("Subclasses must implement apply()")


class AndCombination(FilterCombination):
    """
    AND combination of filters.
    All filters must match for the combination to match.
    """
    def apply(self, values: Dict[str, Any]) -> Q:
        """
        Apply AND combination of filters.
        
        Args:
            values: Dictionary of field names and their values
            
        Returns:
            Q object with AND connector
        """
        result = Q()
        for filter_obj in self.filters:
            # Check if the filter is another combination
            if isinstance(filter_obj, FilterCombination):
                # Apply the nested combination with all values
                filter_q = filter_obj.apply(values)
            else:
                # Get the field name from the filter
                field_name = filter_obj.field_name
                
                # Skip if the field is not in the values
                if field_name not in values:
                    continue
                
                # Apply the filter with the value
                filter_q = filter_obj.apply(values[field_name])
            
            # Combine with AND
            result &= filter_q
        
        return result


class OrCombination(FilterCombination):
    """
    OR combination of filters.
    At least one filter must match for the combination to match.
    """
    def apply(self, values: Dict[str, Any]) -> Q:
        """
        Apply OR combination of filters.
        
        Args:
            values: Dictionary of field names and their values
            
        Returns:
            Q object with OR connector
        """
        result = Q()
        for filter_obj in self.filters:
            # Check if the filter is another combination
            if isinstance(filter_obj, FilterCombination):
                # Apply the nested combination with all values
                filter_q = filter_obj.apply(values)
            else:
                # Get the field name from the filter
                field_name = filter_obj.field_name
                
                # Skip if the field is not in the values
                if field_name not in values:
                    continue
                
                # Apply the filter with the value
                filter_q = filter_obj.apply(values[field_name])
            
            # Combine with OR
            result |= filter_q
        
        return result


class FilterExpression:
    """
    Represents a filter expression with field, operator, and value.
    """
    def __init__(self, field_name: str, operator: str, value: Any):
        """
        Initialize a filter expression.
        
        Args:
            field_name: Name of the field to filter on
            operator: Operator to use for filtering
            value: Value to filter by
        """
        self.field_name = field_name
        self.operator = operator
        self.value = value
    
    def apply(self) -> Q:
        """
        Apply the filter expression.
        
        Returns:
            Q object representing the filter condition
        """
        # For exact matches, use the field name directly
        if self.operator == 'exact':
            return Q(**{self.field_name: self.value})
            
        # For other operators, create a lookup string
        lookup = f"{self.field_name}__{self.operator}"
        return Q(**{lookup: self.value})


class FilterGroup:
    """
    Group of filters that are combined with AND.
    """
    def __init__(self):
        """Initialize an empty filter group."""
        self.filters: Dict[str, BaseFilter] = {}
        self.expressions: List[FilterExpression] = []
    
    def add_filter(self, name: str, filter_obj: BaseFilter) -> None:
        """
        Add a filter to the group.
        
        Args:
            name: Name to identify the filter
            filter_obj: Filter object to add
        """
        self.filters[name] = filter_obj
    
    def add_expression(self, field_name: str, operator: str, value: Any) -> None:
        """
        Add a filter expression to the group.
        
        Args:
            field_name: Name of the field to filter on
            operator: Operator to use for filtering
            value: Value to filter by
        """
        expression = FilterExpression(field_name, operator, value)
        self.expressions.append(expression)
    
    def apply(self, values: Optional[Dict[str, Any]] = None) -> Q:
        """
        Apply all filters and expressions in the group.
        
        Args:
            values: Optional dictionary of field names and their values
            
        Returns:
            Q object representing the combined filter conditions
        """
        result = Q()
        
        # Apply filters if values are provided
        if values:
            for name, filter_obj in self.filters.items():
                # Get the field name from the filter
                field_name = filter_obj.field_name
                
                # Skip if the field is not in the values
                if field_name not in values:
                    continue
                
                # Apply the filter with the value
                filter_q = filter_obj.apply(values[field_name])
                
                # Combine with AND
                result &= filter_q
        
        # Apply expressions
        for expression in self.expressions:
            # Apply the expression
            expression_q = expression.apply()
            
            # Combine with AND
            result &= expression_q
        
        return result


class FilterFactory:
    """
    Factory for creating filter objects based on field type and operator.
    """
    # Mapping of field types to filter classes
    FILTER_TYPES = {
        'text': TextFilter,
        'char': TextFilter,
        'string': TextFilter,
        'integer': NumericFilter,
        'int': NumericFilter,
        'number': NumericFilter,
        'decimal': NumericFilter,
        'float': NumericFilter,
        'date': DateFilter,
        'datetime': DateFilter,
        'time': TimeFilter,
        'boolean': BooleanFilter,
        'bool': BooleanFilter,
        'choice': ChoiceFilter,
        'related': RelatedObjectFilter,
    }
    
    # Mapping of field types to advanced filter classes
    ADVANCED_FILTER_TYPES = {
        'text': AdvancedTextFilter,
        'char': AdvancedTextFilter,
        'string': AdvancedTextFilter,
        'integer': AdvancedNumericFilter,
        'int': AdvancedNumericFilter,
        'number': AdvancedNumericFilter,
        'decimal': AdvancedNumericFilter,
        'float': AdvancedNumericFilter,
        'date': AdvancedDateFilter,
        'datetime': AdvancedDateFilter,
        'time': AdvancedTimeFilter,
        'boolean': AdvancedBooleanFilter,
        'bool': AdvancedBooleanFilter,
        'choice': AdvancedChoiceFilter,
        'related': AdvancedRelatedObjectFilter,
    }
    
    @staticmethod
    def create_filter(field_name: str, field_type: str, operator: Optional[str] = None, **kwargs) -> BaseFilter:
        """
        Create a filter object based on field type and operator.
        
        Args:
            field_name: Name of the field to filter on
            field_type: Type of the field
            operator: Optional operator to use for filtering
            **kwargs: Additional arguments for the filter
            
        Returns:
            Filter object
            
        Raises:
            ValueError: If field type is invalid or operator is invalid
        """
        # Normalize field type
        field_type = field_type.lower()
        
        # Check if field type is valid
        if field_type not in FilterFactory.FILTER_TYPES:
            raise ValueError(f"Invalid field type: {field_type}")
        
        # If operator is provided, use advanced filter
        if operator:
            # Check if field type is valid for advanced filter
            if field_type not in FilterFactory.ADVANCED_FILTER_TYPES:
                raise ValueError(f"Field type {field_type} does not support advanced filters")
            
            # Get the advanced filter class
            filter_class = FilterFactory.ADVANCED_FILTER_TYPES[field_type]
            
            # Create the filter with operator
            return filter_class(field_name, operator=operator, **kwargs)
        else:
            # Get the basic filter class
            filter_class = FilterFactory.FILTER_TYPES[field_type]
            
            # Create the filter
            return filter_class(field_name, **kwargs) 