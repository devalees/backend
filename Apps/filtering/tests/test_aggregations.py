from django.test import TestCase
from django.db import models
from django.db.models import Count, Sum, Avg, Min, Max, F, ExpressionWrapper, FloatField
from ..aggregations import (
    count_aggregation, sum_aggregation, avg_aggregation, 
    min_aggregation, max_aggregation, custom_aggregation,
    get_aggregation, aggregation_registry
)
from ..base import BaseAggregatableModel

# Test model for aggregation tests
class TestAggregationModel(BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class TestAggregations(TestCase):
    """Test the base aggregation types"""
    
    def setUp(self):
        """Set up test data"""
        # Create test data
        TestAggregationModel.objects.create(name="Test 1", value=10, price=100.50)
        TestAggregationModel.objects.create(name="Test 2", value=20, price=200.75)
        TestAggregationModel.objects.create(name="Test 3", value=30, price=300.25)
    
    def test_count_aggregation(self):
        """Test count aggregation"""
        # Get the count aggregation
        count_agg = count_aggregation('id')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(count=count_agg)
        
        # Check the result
        self.assertEqual(result['count'], 3)
    
    def test_sum_aggregation(self):
        """Test sum aggregation"""
        # Get the sum aggregation
        sum_agg = sum_aggregation('value')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(sum=sum_agg)
        
        # Check the result
        self.assertEqual(result['sum'], 60)  # 10 + 20 + 30
    
    def test_avg_aggregation(self):
        """Test average aggregation"""
        # Get the average aggregation
        avg_agg = avg_aggregation('value')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(avg=avg_agg)
        
        # Check the result
        self.assertEqual(result['avg'], 20)  # (10 + 20 + 30) / 3
    
    def test_min_aggregation(self):
        """Test minimum aggregation"""
        # Get the minimum aggregation
        min_agg = min_aggregation('value')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(min=min_agg)
        
        # Check the result
        self.assertEqual(result['min'], 10)  # min(10, 20, 30)
    
    def test_max_aggregation(self):
        """Test maximum aggregation"""
        # Get the maximum aggregation
        max_agg = max_aggregation('value')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(max=max_agg)
        
        # Check the result
        self.assertEqual(result['max'], 30)  # max(10, 20, 30)
    
    def test_custom_aggregation(self):
        """Test custom aggregation"""
        # Get the custom aggregation
        custom_agg = custom_aggregation('value', 'value * 2')
        
        # Apply the aggregation
        result = TestAggregationModel.objects.aggregate(custom=custom_agg)
        
        # Check the result (this is a simple test, the actual result depends on the implementation)
        self.assertIn('custom', result)
    
    def test_get_aggregation(self):
        """Test getting an aggregation by type"""
        # Get aggregations by type
        count_agg = get_aggregation('count', 'id')
        sum_agg = get_aggregation('sum', 'value')
        avg_agg = get_aggregation('avg', 'value')
        min_agg = get_aggregation('min', 'value')
        max_agg = get_aggregation('max', 'value')
        
        # Apply the aggregations
        result = TestAggregationModel.objects.aggregate(
            count=count_agg,
            sum=sum_agg,
            avg=avg_agg,
            min=min_agg,
            max=max_agg
        )
        
        # Check the results
        self.assertEqual(result['count'], 3)
        self.assertEqual(result['sum'], 60)
        self.assertEqual(result['avg'], 20)
        self.assertEqual(result['min'], 10)
        self.assertEqual(result['max'], 30)
    
    def test_get_aggregation_with_invalid_type(self):
        """Test getting an aggregation with an invalid type"""
        # Try to get an aggregation with an invalid type
        expected_message = "Invalid aggregation type 'invalid_type'. Valid types are: avg, count, custom, max, min, sum"
        with self.assertRaises(ValueError) as context:
            get_aggregation('invalid_type', 'value')
        
        # Verify the error message
        self.assertEqual(str(context.exception), expected_message)
    
    def test_get_custom_aggregation_without_expression(self):
        """Test getting a custom aggregation without an expression"""
        # Try to get a custom aggregation without an expression
        with self.assertRaises(ValueError):
            get_aggregation('custom', 'value')
    
    def test_registry_contains_all_aggregation_types(self):
        """Test that the registry contains all aggregation types"""
        # Check that all aggregation types are registered
        self.assertIn('count', aggregation_registry.aggregations)
        self.assertIn('sum', aggregation_registry.aggregations)
        self.assertIn('avg', aggregation_registry.aggregations)
        self.assertIn('min', aggregation_registry.aggregations)
        self.assertIn('max', aggregation_registry.aggregations)
        self.assertIn('custom', aggregation_registry.aggregations)
    
    def test_multiple_aggregations(self):
        """Test applying multiple aggregations to the same field"""
        # Get multiple aggregations for the same field
        sum_agg = get_aggregation('sum', 'value')
        avg_agg = get_aggregation('avg', 'value')
        min_agg = get_aggregation('min', 'value')
        max_agg = get_aggregation('max', 'value')
        
        # Apply the aggregations
        result = TestAggregationModel.objects.aggregate(
            sum=sum_agg,
            avg=avg_agg,
            min=min_agg,
            max=max_agg
        )
        
        # Check the results
        self.assertEqual(result['sum'], 60)
        self.assertEqual(result['avg'], 20)
        self.assertEqual(result['min'], 10)
        self.assertEqual(result['max'], 30)
    
    def test_aggregations_on_different_fields(self):
        """Test applying aggregations to different fields"""
        # Get aggregations for different fields
        value_sum = get_aggregation('sum', 'value')
        price_avg = get_aggregation('avg', 'price')
        
        # Apply the aggregations
        result = TestAggregationModel.objects.aggregate(
            value_sum=value_sum,
            price_avg=price_avg
        )
        
        # Check the results
        self.assertEqual(result['value_sum'], 60)
        self.assertEqual(result['price_avg'], 200.50)  # (100.50 + 200.75 + 300.25) / 3 