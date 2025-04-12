import pytest
from django.db import models
from django.db.models import Q
from typing import Dict, Any, List, Union
from ..filters import (
    BaseFilter, TextFilter, NumericFilter, DateFilter, 
    TimeFilter, BooleanFilter, ChoiceFilter, RelatedObjectFilter
)
from ..advanced_filters import (
    AdvancedTextFilter, AdvancedNumericFilter, AdvancedDateFilter,
    AdvancedTimeFilter, AdvancedBooleanFilter, AdvancedChoiceFilter,
    AdvancedRelatedObjectFilter
)
from ..filter_combinations import (
    FilterCombination, AndCombination, OrCombination, 
    FilterGroup, FilterExpression, FilterFactory
)
from datetime import datetime, date, time

# Test models
class FilterCombinationTestModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering'
        managed = False  # Don't create actual database tables

# Test cases for FilterCombination
class TestFilterCombination:
    def test_and_combination(self):
        """Test AND combination of filters"""
        # Create filters
        name_filter = TextFilter('name')
        age_filter = NumericFilter('age')
        
        # Create AND combination
        and_filter = AndCombination([name_filter, age_filter])
        
        # Apply filters with values
        result = and_filter.apply({'name': 'John', 'age': 30})
        
        # Check that the result is a Q object with AND operation
        assert isinstance(result, Q)
        assert result.connector == Q.AND
        
        # Check that both filters are included
        assert len(result.children) == 2
        
        # Check that the filters are applied correctly
        name_q = result.children[0]
        age_q = result.children[1]
        
        assert name_q[0] == 'name__icontains'
        assert name_q[1] == 'John'
        assert age_q[0] == 'age'
        assert age_q[1] == 30
    
    def test_or_combination(self):
        """Test OR combination of filters"""
        # Create filters
        name_filter = TextFilter('name')
        age_filter = NumericFilter('age')
        
        # Create OR combination
        or_filter = OrCombination([name_filter, age_filter])
        
        # Apply filters with values
        result = or_filter.apply({'name': 'John', 'age': 30})
        
        # Check that the result is a Q object with OR operation
        assert isinstance(result, Q)
        assert result.connector == Q.OR
        
        # Check that both filters are included
        assert len(result.children) == 2
        
        # Check that the filters are applied correctly
        name_q = result.children[0]
        age_q = result.children[1]
        
        assert name_q[0] == 'name__icontains'
        assert name_q[1] == 'John'
        assert age_q[0] == 'age'
        assert age_q[1] == 30
    
    def test_nested_combinations(self):
        """Test nested combinations of filters"""
        # Create filters
        name_filter = TextFilter('name')
        age_filter = NumericFilter('age')
        is_active_filter = BooleanFilter('is_active')
        
        # Create nested combinations: (name AND age) OR is_active
        inner_and = AndCombination([name_filter, age_filter])
        outer_or = OrCombination([inner_and, is_active_filter])
        
        # Apply filters with values
        result = outer_or.apply({'name': 'John', 'age': 30, 'is_active': True})
        
        # Check that the result is a Q object with OR operation
        assert isinstance(result, Q)
        assert result.connector == Q.OR
        
        # Check that both parts of the OR are included
        assert len(result.children) == 2
        
        # Check the inner AND combination
        inner_and_q = result.children[0]
        assert inner_and_q.connector == Q.AND
        assert len(inner_and_q.children) == 2
        
        # Check the is_active filter
        is_active_q = result.children[1]
        assert is_active_q[0] == 'is_active'
        assert is_active_q[1] is True

# Test cases for FilterGroup
class TestFilterGroup:
    def test_filter_group(self):
        """Test FilterGroup with multiple filters"""
        # Create a filter group
        group = FilterGroup()
        
        # Add filters to the group
        group.add_filter('name', TextFilter('name'))
        group.add_filter('age', NumericFilter('age'))
        group.add_filter('is_active', BooleanFilter('is_active'))
        
        # Apply the group with values
        result = group.apply({
            'name': 'John',
            'age': 30,
            'is_active': True
        })
        
        # Check that the result is a Q object with AND operation
        assert isinstance(result, Q)
        assert result.connector == Q.AND
        
        # Check that all filters are included
        assert len(result.children) == 3
    
    def test_filter_group_with_missing_values(self):
        """Test FilterGroup with missing values"""
        # Create a filter group
        group = FilterGroup()
        
        # Add filters to the group
        group.add_filter('name', TextFilter('name'))
        group.add_filter('age', NumericFilter('age'))
        
        # Apply the group with only some values
        result = group.apply({
            'name': 'John'
            # 'age' is missing
        })
        
        # Check that the result is a Q object with AND operation
        assert isinstance(result, Q)
        assert result.connector == Q.AND
        
        # Check that only the provided filter is included
        assert len(result.children) == 1
        
        # Check that the filter is applied correctly
        name_q = result.children[0]
        assert name_q[0] == 'name__icontains'
        assert name_q[1] == 'John'

# Test cases for FilterExpression
class TestFilterExpression:
    def test_simple_expression(self):
        """Test simple filter expression"""
        # Create a filter expression
        expression = FilterExpression('name', 'contains', 'John')
        
        # Apply the expression
        result = expression.apply()
        
        # Check that the result is a Q object
        assert isinstance(result, Q)
        
        # Check that the filter is applied correctly
        assert result.children[0][0] == 'name__contains'
        assert result.children[0][1] == 'John'
    
    def test_advanced_expression(self):
        """Test advanced filter expression"""
        # Create an advanced filter expression
        expression = FilterExpression('age', 'gt', 30)
        
        # Apply the expression
        result = expression.apply()
        
        # Check that the result is a Q object
        assert isinstance(result, Q)
        
        # Check that the filter is applied correctly
        assert result.children[0][0] == 'age__gt'
        assert result.children[0][1] == 30

# Test cases for FilterFactory
class TestFilterFactory:
    def test_create_text_filter(self):
        """Test creating a text filter"""
        # Create a text filter
        filter_obj = FilterFactory.create_filter('name', 'text')
        
        # Check that the filter is of the correct type
        assert isinstance(filter_obj, TextFilter)
        assert filter_obj.field_name == 'name'
    
    def test_create_numeric_filter(self):
        """Test creating a numeric filter"""
        # Create a numeric filter
        filter_obj = FilterFactory.create_filter('age', 'integer')
        
        # Check that the filter is of the correct type
        assert isinstance(filter_obj, NumericFilter)
        assert filter_obj.field_name == 'age'
    
    def test_create_advanced_filter(self):
        """Test creating an advanced filter"""
        # Create an advanced text filter
        filter_obj = FilterFactory.create_filter('name', 'text', operator='startswith')
        
        # Check that the filter is of the correct type
        assert isinstance(filter_obj, AdvancedTextFilter)
        assert filter_obj.field_name == 'name'
        assert filter_obj.operator == 'startswith'
    
    def test_create_invalid_filter(self):
        """Test creating an invalid filter"""
        # Try to create a filter with an invalid type
        with pytest.raises(ValueError):
            FilterFactory.create_filter('name', 'invalid_type')
    
    def test_create_invalid_operator(self):
        """Test creating a filter with an invalid operator"""
        # Try to create a filter with an invalid operator
        with pytest.raises(ValueError):
            FilterFactory.create_filter('name', 'text', operator='invalid_operator')

# Test cases for complex filter combinations
class TestComplexFilterCombinations:
    def test_complex_and_or_combination(self):
        """Test complex AND/OR combination"""
        # Create a complex filter: (name contains 'John' AND age > 30) OR (is_active = True AND created_at > '2023-01-01')
        
        # Create the first part: name contains 'John' AND age > 30
        name_filter = FilterFactory.create_filter('name', 'text', operator='contains')
        age_filter = FilterFactory.create_filter('age', 'integer', operator='gt')
        first_part = AndCombination([name_filter, age_filter])
        
        # Create the second part: is_active = True AND created_at > '2023-01-01'
        is_active_filter = FilterFactory.create_filter('is_active', 'boolean')
        created_at_filter = FilterFactory.create_filter('created_at', 'datetime', operator='gt')
        second_part = AndCombination([is_active_filter, created_at_filter])
        
        # Combine the parts with OR
        complex_filter = OrCombination([first_part, second_part])
        
        # Apply the complex filter
        result = complex_filter.apply({
            'name': 'John',
            'age': 30,
            'is_active': True,
            'created_at': datetime(2023, 1, 1)
        })
        
        # Check that the result is a Q object with OR operation
        assert isinstance(result, Q)
        assert result.connector == Q.OR
        
        # Check that both parts of the OR are included
        assert len(result.children) == 2
        
        # Check the first part (AND)
        first_part_q = result.children[0]
        assert first_part_q.connector == Q.AND
        assert len(first_part_q.children) == 2
        
        # Check the second part (AND)
        second_part_q = result.children[1]
        assert second_part_q.connector == Q.AND
        assert len(second_part_q.children) == 2
    
    def test_filter_group_with_expressions(self):
        """Test FilterGroup with expressions"""
        # Create a filter group
        group = FilterGroup()
        
        # Add expressions to the group
        group.add_expression('name', 'contains', 'John')
        group.add_expression('age', 'gt', 30)
        group.add_expression('is_active', 'exact', True)
        
        # Apply the group
        result = group.apply()
        
        # Check that the result is a Q object with AND operation
        assert isinstance(result, Q)
        assert result.connector == Q.AND
        
        # Check that all expressions are included
        assert len(result.children) == 3
        
        # Check that the expressions are applied correctly
        name_q = result.children[0]
        age_q = result.children[1]
        is_active_q = result.children[2]
        
        assert name_q[0] == 'name__contains'
        assert name_q[1] == 'John'
        assert age_q[0] == 'age__gt'
        assert age_q[1] == 30
        assert is_active_q[0] == 'is_active'
        assert is_active_q[1] is True 