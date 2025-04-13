from django.test import TestCase
from django.db import models
from django.db.models import Count, Sum, Avg, Min, Max, F, ExpressionWrapper, FloatField
from ..aggregations import (
    count_aggregation, sum_aggregation, avg_aggregation, 
    min_aggregation, max_aggregation, custom_aggregation,
    get_aggregation, aggregation_registry
)
from ..aggregation_grouping import (
    create_group_by_aggregation, create_multiple_aggregations,
    create_nested_aggregations, apply_group_by_aggregations
)
from ..base import BaseAggregatableModel

# Test model for aggregation grouping tests
class TestGroupingModel(BaseAggregatableModel):
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class TestAggregationGrouping(TestCase):
    """Test the aggregation grouping system"""
    
    def setUp(self):
        """Set up test data"""
        # Create test data with categories and subcategories
        TestGroupingModel.objects.create(
            category="Electronics", subcategory="Phones", 
            name="iPhone", value=10, price=1000.50
        )
        TestGroupingModel.objects.create(
            category="Electronics", subcategory="Phones", 
            name="Samsung", value=15, price=800.75
        )
        TestGroupingModel.objects.create(
            category="Electronics", subcategory="Laptops", 
            name="MacBook", value=20, price=2000.25
        )
        TestGroupingModel.objects.create(
            category="Electronics", subcategory="Laptops", 
            name="Dell", value=25, price=1500.50
        )
        TestGroupingModel.objects.create(
            category="Clothing", subcategory="Shirts", 
            name="T-Shirt", value=5, price=20.00
        )
        TestGroupingModel.objects.create(
            category="Clothing", subcategory="Shirts", 
            name="Polo", value=8, price=40.00
        )
        TestGroupingModel.objects.create(
            category="Clothing", subcategory="Pants", 
            name="Jeans", value=12, price=60.00
        )
        TestGroupingModel.objects.create(
            category="Clothing", subcategory="Pants", 
            name="Khakis", value=10, price=50.00
        )
    
    def test_group_by_single_field(self):
        """Test grouping by a single field"""
        # Create a group by aggregation for the category field
        group_by_agg = create_group_by_aggregation('category', queryset=TestGroupingModel.objects.all())
        
        # Apply the group by aggregation
        result = apply_group_by_aggregations(
            TestGroupingModel.objects.all(),
            group_by_agg
        )
        
        # Check the result
        self.assertEqual(len(result), 2)  # Two categories: Electronics and Clothing
        
        # Check the Electronics category
        electronics = next(item for item in result if item['category'] == 'Electronics')
        self.assertEqual(electronics['count'], 4)  # 4 items in Electronics
        
        # Check the Clothing category
        clothing = next(item for item in result if item['category'] == 'Clothing')
        self.assertEqual(clothing['count'], 4)  # 4 items in Clothing
    
    def test_group_by_multiple_fields(self):
        """Test grouping by multiple fields"""
        # Create a group by aggregation for the category and subcategory fields
        group_by_agg = create_group_by_aggregation(['category', 'subcategory'], queryset=TestGroupingModel.objects.all())
        
        # Apply the group by aggregation
        result = apply_group_by_aggregations(
            TestGroupingModel.objects.all(),
            group_by_agg
        )
        
        # Check the result
        self.assertEqual(len(result), 4)  # Four combinations: Electronics/Phones, Electronics/Laptops, Clothing/Shirts, Clothing/Pants
        
        # Check the Electronics/Phones combination
        electronics_phones = next(item for item in result if item['category'] == 'Electronics' and item['subcategory'] == 'Phones')
        self.assertEqual(electronics_phones['count'], 2)  # 2 items in Electronics/Phones
        
        # Check the Electronics/Laptops combination
        electronics_laptops = next(item for item in result if item['category'] == 'Electronics' and item['subcategory'] == 'Laptops')
        self.assertEqual(electronics_laptops['count'], 2)  # 2 items in Electronics/Laptops
        
        # Check the Clothing/Shirts combination
        clothing_shirts = next(item for item in result if item['category'] == 'Clothing' and item['subcategory'] == 'Shirts')
        self.assertEqual(clothing_shirts['count'], 2)  # 2 items in Clothing/Shirts
        
        # Check the Clothing/Pants combination
        clothing_pants = next(item for item in result if item['category'] == 'Clothing' and item['subcategory'] == 'Pants')
        self.assertEqual(clothing_pants['count'], 2)  # 2 items in Clothing/Pants
    
    def test_multiple_aggregations(self):
        """Test applying multiple aggregations to grouped data"""
        # Create a group by aggregation for the category field
        group_by_agg = create_group_by_aggregation('category', queryset=TestGroupingModel.objects.all())
        
        # Create multiple aggregations
        multiple_agg = create_multiple_aggregations([
            ('sum', 'value'),
            ('avg', 'price'),
            ('min', 'value'),
            ('max', 'price')
        ])
        
        # Apply the group by aggregation with multiple aggregations
        result = apply_group_by_aggregations(
            TestGroupingModel.objects.all(),
            group_by_agg,
            multiple_agg
        )
        
        # Check the result
        self.assertEqual(len(result), 2)  # Two categories: Electronics and Clothing
        
        # Check the Electronics category
        electronics = next(item for item in result if item['category'] == 'Electronics')
        self.assertEqual(electronics['count'], 4)  # 4 items in Electronics
        self.assertEqual(electronics['value_sum'], 70)  # 10 + 15 + 20 + 25
        self.assertEqual(electronics['price_avg'], 1325.50)  # (1000.50 + 800.75 + 2000.25 + 1500.50) / 4
        self.assertEqual(electronics['value_min'], 10)  # min(10, 15, 20, 25)
        self.assertEqual(electronics['price_max'], 2000.25)  # max(1000.50, 800.75, 2000.25, 1500.50)
        
        # Check the Clothing category
        clothing = next(item for item in result if item['category'] == 'Clothing')
        self.assertEqual(clothing['count'], 4)  # 4 items in Clothing
        self.assertEqual(clothing['value_sum'], 35)  # 5 + 8 + 12 + 10
        self.assertEqual(clothing['price_avg'], 42.50)  # (20.00 + 40.00 + 60.00 + 50.00) / 4
        self.assertEqual(clothing['value_min'], 5)  # min(5, 8, 12, 10)
        self.assertEqual(clothing['price_max'], 60.00)  # max(20.00, 40.00, 60.00, 50.00)
    
    def test_nested_aggregations(self):
        """Test applying nested aggregations to grouped data"""
        # Create a group by aggregation for the category and subcategory fields
        group_by_agg = create_group_by_aggregation(['category', 'subcategory'], queryset=TestGroupingModel.objects.all())
        
        # Create nested aggregations
        nested_agg = create_nested_aggregations([
            ('sum', 'value'),
            ('avg', 'price')
        ])
        
        # Apply the group by aggregation with nested aggregations
        result = apply_group_by_aggregations(
            TestGroupingModel.objects.all(),
            group_by_agg,
            multiple_agg=None,
            nested_agg=nested_agg
        )
        
        # Check the result
        self.assertEqual(len(result), 4)  # Four combinations: Electronics/Phones, Electronics/Laptops, Clothing/Shirts, Clothing/Pants
        
        # Check the Electronics/Phones combination
        electronics_phones = next(item for item in result if item['category'] == 'Electronics' and item['subcategory'] == 'Phones')
        self.assertEqual(electronics_phones['count'], 2)  # 2 items in Electronics/Phones
        self.assertEqual(electronics_phones['value_sum'], 25)  # 10 + 15
        self.assertEqual(electronics_phones['price_avg'], 900.625)  # (1000.50 + 800.75) / 2
        
        # Check the Electronics/Laptops combination
        electronics_laptops = next(item for item in result if item['category'] == 'Electronics' and item['subcategory'] == 'Laptops')
        self.assertEqual(electronics_laptops['count'], 2)  # 2 items in Electronics/Laptops
        self.assertEqual(electronics_laptops['value_sum'], 45)  # 20 + 25
        self.assertEqual(electronics_laptops['price_avg'], 1750.375)  # (2000.25 + 1500.50) / 2
        
        # Check the Clothing/Shirts combination
        clothing_shirts = next(item for item in result if item['category'] == 'Clothing' and item['subcategory'] == 'Shirts')
        self.assertEqual(clothing_shirts['count'], 2)  # 2 items in Clothing/Shirts
        self.assertEqual(clothing_shirts['value_sum'], 13)  # 5 + 8
        self.assertEqual(clothing_shirts['price_avg'], 30.00)  # (20.00 + 40.00) / 2
        
        # Check the Clothing/Pants combination
        clothing_pants = next(item for item in result if item['category'] == 'Clothing' and item['subcategory'] == 'Pants')
        self.assertEqual(clothing_pants['count'], 2)  # 2 items in Clothing/Pants
        self.assertEqual(clothing_pants['value_sum'], 22)  # 12 + 10
        self.assertEqual(clothing_pants['price_avg'], 55.00)  # (60.00 + 50.00) / 2
    
    def test_invalid_group_by_field(self):
        """Test that using an invalid field name raises a ValueError"""
        with self.assertRaises(ValueError):
            # Create a group by aggregation with an invalid field
            group_by_agg = create_group_by_aggregation('invalid_field', queryset=TestGroupingModel.objects.all())
    
    def test_invalid_multiple_aggregations(self):
        """Test applying invalid multiple aggregations"""
        # Try to apply invalid multiple aggregations
        with self.assertRaises(ValueError):
            create_multiple_aggregations([
                ('invalid_type', 'value')
            ])
    
    def test_invalid_nested_aggregations(self):
        """Test applying invalid nested aggregations"""
        # Try to apply invalid nested aggregations
        with self.assertRaises(ValueError):
            create_nested_aggregations([
                ('invalid_type', 'value')
            ])
    
    def test_empty_group_by_fields(self):
        """Test grouping by empty fields"""
        # Try to group by empty fields
        with self.assertRaises(ValueError):
            create_group_by_aggregation([])
    
    def test_empty_multiple_aggregations(self):
        """Test applying empty multiple aggregations"""
        # Try to apply empty multiple aggregations
        with self.assertRaises(ValueError):
            create_multiple_aggregations([])
    
    def test_empty_nested_aggregations(self):
        """Test applying empty nested aggregations"""
        # Try to apply empty nested aggregations
        with self.assertRaises(ValueError):
            create_nested_aggregations([]) 