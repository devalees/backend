from django.test import TestCase
from django.db import models
from django.db.models import Sum, Avg, Min, Max, Count
from ..mixins import AggregatableMixin
from ..base import BaseAggregatableModel

# Test model for aggregation tests
class TestAggregatableMixinModel(BaseAggregatableModel, AggregatableMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class TestAggregatableMixin(TestCase):
    """Test the AggregatableMixin with the new aggregation functions"""
    
    def setUp(self):
        """Set up test data"""
        # Create test data
        TestAggregatableMixinModel.objects.create(name="Test 1", value=10, price=100.50)
        TestAggregatableMixinModel.objects.create(name="Test 2", value=20, price=200.75)
        TestAggregatableMixinModel.objects.create(name="Test 3", value=30, price=300.25)
    
    def test_get_aggregatable_fields(self):
        """Test getting aggregatable fields"""
        # Get aggregatable fields
        fields = TestAggregatableMixinModel.get_aggregatable_fields()
        
        # Check that the fields are correct
        self.assertIn('value', fields)
        self.assertIn('price', fields)
        self.assertNotIn('name', fields)
        
        # Check field types
        self.assertEqual(fields['value']['type'], 'integer')
        self.assertEqual(fields['price']['type'], 'decimal')
    
    def test_aggregate_with_count(self):
        """Test aggregating with count"""
        # Apply count aggregation
        result = TestAggregatableMixinModel.aggregate({'id': 'count'})
        
        # Check the result
        self.assertEqual(result['id__count'], 3)
    
    def test_aggregate_with_sum(self):
        """Test aggregating with sum"""
        # Apply sum aggregation
        result = TestAggregatableMixinModel.aggregate({'value': 'sum'})
        
        # Check the result
        self.assertEqual(result['value__sum'], 60)  # 10 + 20 + 30
    
    def test_aggregate_with_avg(self):
        """Test aggregating with average"""
        # Apply average aggregation
        result = TestAggregatableMixinModel.aggregate({'value': 'avg'})
        
        # Check the result
        self.assertEqual(result['value__avg'], 20)  # (10 + 20 + 30) / 3
    
    def test_aggregate_with_min(self):
        """Test aggregating with minimum"""
        # Apply minimum aggregation
        result = TestAggregatableMixinModel.aggregate({'value': 'min'})
        
        # Check the result
        self.assertEqual(result['value__min'], 10)  # min(10, 20, 30)
    
    def test_aggregate_with_max(self):
        """Test aggregating with maximum"""
        # Apply maximum aggregation
        result = TestAggregatableMixinModel.aggregate({'value': 'max'})
        
        # Check the result
        self.assertEqual(result['value__max'], 30)  # max(10, 20, 30)
    
    def test_aggregate_with_multiple_types(self):
        """Test aggregating with multiple types"""
        # Apply multiple aggregations
        result = TestAggregatableMixinModel.aggregate({
            'value': ['sum', 'avg', 'min', 'max'],
            'price': ['sum', 'avg']
        })
        
        # Check the results
        self.assertEqual(result['value__sum'], 60)
        self.assertEqual(result['value__avg'], 20)
        self.assertEqual(result['value__min'], 10)
        self.assertEqual(result['value__max'], 30)
        self.assertEqual(result['price__sum'], 601.50)  # 100.50 + 200.75 + 300.25
        self.assertEqual(result['price__avg'], 200.50)  # (100.50 + 200.75 + 300.25) / 3
    
    def test_aggregate_with_group_by(self):
        """Test aggregating with group by"""
        # Create test data with groups
        TestAggregatableMixinModel.objects.create(name="Group 1", value=40, price=400.00)
        TestAggregatableMixinModel.objects.create(name="Group 1", value=50, price=500.00)
        TestAggregatableMixinModel.objects.create(name="Group 2", value=60, price=600.00)
        
        # Apply aggregation with group by
        result = TestAggregatableMixinModel.aggregate(
            {'value': ['sum', 'avg']},
            group_by=['name']
        )
        
        # Check the results
        self.assertEqual(len(result), 5)  # 5 groups: Test 1, Test 2, Test 3, Group 1, Group 2
        
        # Find Group 1
        group1 = next(g for g in result if g['name'] == 'Group 1')
        self.assertEqual(group1['value__sum'], 90)  # 40 + 50
        self.assertEqual(group1['value__avg'], 45)  # (40 + 50) / 2
        
        # Find Group 2
        group2 = next(g for g in result if g['name'] == 'Group 2')
        self.assertEqual(group2['value__sum'], 60)
        self.assertEqual(group2['value__avg'], 60)
    
    def test_aggregate_with_invalid_field(self):
        """Test aggregating with an invalid field"""
        # Try to aggregate with an invalid field
        with self.assertRaises(ValueError):
            TestAggregatableMixinModel.aggregate({'invalid_field': 'sum'})
    
    def test_aggregate_with_invalid_aggregation(self):
        """Test aggregating with an invalid aggregation type"""
        # Try to aggregate with an invalid aggregation type
        with self.assertRaises(ValueError):
            TestAggregatableMixinModel.aggregate({'value': 'invalid_aggregation'})
    
    def test_aggregate_with_invalid_group_by(self):
        """Test aggregating with an invalid group by field"""
        # Try to aggregate with an invalid group by field
        with self.assertRaises(ValueError):
            TestAggregatableMixinModel.aggregate(
                {'value': 'sum'},
                group_by=['invalid_field']
            ) 