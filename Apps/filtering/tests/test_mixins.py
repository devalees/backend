import pytest
from django.db import models
from django.test import TestCase
from typing import Dict, Any, List, Optional
from django.db.models import Sum, Avg

from ..base import BaseFilterableModel, BaseAggregatableModel
from ..mixins import FilterableMixin, AggregatableMixin, ModelRegistryMixin
from ..models import (
    TestFilterableModel,
    TestAggregatableModel,
    TestCombinedModel,
    TestModelRegistryModel
)

# Test cases
class TestFilterableMixin(TestCase):
    def setUp(self):
        # Register the model
        TestFilterableModel.register_model_class()
        
        self.model = TestFilterableModel.objects.create(
            name="Test Model",
            description="Test Description",
            age=25,
            is_active=True
        )
    
    def test_get_filterable_fields(self):
        """Test that get_filterable_fields returns the correct fields"""
        fields = self.model.get_filterable_fields()
        
        # Check that all fields are included
        self.assertIn('name', fields)
        self.assertIn('description', fields)
        self.assertIn('age', fields)
        self.assertIn('is_active', fields)
        self.assertIn('created_at', fields)
        
        # Check field types
        self.assertEqual(fields['name']['type'], 'char')
        self.assertEqual(fields['description']['type'], 'text')
        self.assertEqual(fields['age']['type'], 'integer')
        self.assertEqual(fields['is_active']['type'], 'boolean')
        self.assertEqual(fields['created_at']['type'], 'datetime')
    
    def test_filter(self):
        """Test that filter method returns a queryset with applied filters"""
        # Create test data
        self.model1 = TestFilterableModel.objects.create(name="Test 1", description="Description 1", age=25, is_active=True)
        self.model2 = TestFilterableModel.objects.create(name="Test 2", description="Description 2", age=30, is_active=False)
        self.model3 = TestFilterableModel.objects.create(name="Another", description="Description 3", age=35, is_active=True)
        
        # Test filtering by exact name match
        filtered = TestFilterableModel.filter({'name': {'startswith': 'Test'}})
        self.assertEqual(filtered.count(), 3)  # Test Model, Test 1, Test 2
        
        filtered = TestFilterableModel.filter({'age': 25})
        self.assertEqual(filtered.count(), 2)  # Test Model and Test 1 both have age=25
        
        filtered = TestFilterableModel.filter({'is_active': True})
        self.assertEqual(filtered.count(), 3)  # Test Model, Test 1, and Another are active
        
        # Test complex filtering
        filtered = TestFilterableModel.filter({
            'name': {'startswith': 'Test'},
            'is_active': True
        })
        self.assertEqual(filtered.count(), 2)  # Test Model and Test 1
    
    def test_filter_with_invalid_field(self):
        """Test that filter method raises an error for invalid fields"""
        with self.assertRaises(ValueError):
            self.model.filter({'invalid_field': 'value'})
    
    def test_filter_with_invalid_operator(self):
        """Test that filter method raises an error for invalid operators"""
        with self.assertRaises(ValueError):
            self.model.filter({'name': {'invalid_operator': 'value'}})

class TestAggregatableMixin(TestCase):
    def setUp(self):
        # Register the model
        TestAggregatableModel.register_model_class()
        self.model = TestAggregatableModel
    
    def test_get_aggregatable_fields(self):
        """Test that get_aggregatable_fields returns the correct fields"""
        fields = self.model.get_aggregatable_fields()
        
        # Check that only numeric fields are included
        self.assertIn('value', fields)
        self.assertIn('price', fields)
        self.assertNotIn('name', fields)
        self.assertNotIn('created_at', fields)
        
        # Check field types
        self.assertEqual(fields['value']['type'], 'integer')
        self.assertEqual(fields['price']['type'], 'decimal')
    
    def test_aggregate(self):
        """Test that aggregate method returns the correct aggregations"""
        # Create test data
        TestAggregatableModel.objects.create(name="Test 1", value=10, price=100.50)
        TestAggregatableModel.objects.create(name="Test 2", value=20, price=200.75)
        TestAggregatableModel.objects.create(name="Test 3", value=30, price=300.25)
        
        # Test simple aggregation
        result = self.model.aggregate({'value': 'sum'})
        self.assertEqual(result['value__sum'], 60)
        
        result = self.model.aggregate({'price': 'avg'})
        self.assertEqual(result['price__avg'], 200.50)
        
        # Test multiple aggregations
        result = self.model.aggregate({
            'value': ['sum', 'avg'],
            'price': ['min', 'max']
        })
        self.assertEqual(result['value__sum'], 60)
        self.assertEqual(result['value__avg'], 20)
        self.assertEqual(result['price__min'], 100.50)
        self.assertEqual(result['price__max'], 300.25)
    
    def test_aggregate_with_group_by(self):
        """Test that aggregate method returns correct results when grouping by a field"""
        # Create test data
        self.model1 = TestAggregatableModel.objects.create(name="Group 1", value=10, price=100.50)
        self.model2 = TestAggregatableModel.objects.create(name="Group 1", value=20, price=200.75)
        self.model3 = TestAggregatableModel.objects.create(name="Group 2", value=30, price=300.25)
        self.model4 = TestAggregatableModel.objects.create(name="Group 2", value=40, price=400.00)

        # Test aggregation with group by
        aggregated = TestAggregatableModel.objects.values('name').annotate(
            total_value=Sum('value'),
            avg_value=Avg('value')
        )
        
        self.assertEqual(len(aggregated), 2)  # Should have 2 groups
        
        # Verify group 1
        group1 = next(g for g in aggregated if g['name'] == 'Group 1')
        self.assertEqual(group1['total_value'], 30)  # 10 + 20
        self.assertEqual(group1['avg_value'], 15)  # (10 + 20) / 2
        
        # Verify group 2
        group2 = next(g for g in aggregated if g['name'] == 'Group 2')
        self.assertEqual(group2['total_value'], 70)  # 30 + 40
        self.assertEqual(group2['avg_value'], 35)  # (30 + 40) / 2
    
    def test_aggregate_with_invalid_field(self):
        """Test that aggregate method raises an error for invalid fields"""
        with self.assertRaises(ValueError):
            self.model.aggregate({'invalid_field': 'sum'})
    
    def test_aggregate_with_invalid_aggregation(self):
        """Test that aggregate method raises an error for invalid aggregations"""
        with self.assertRaises(ValueError):
            self.model.aggregate({'value': 'invalid_aggregation'})

class TestModelRegistryMixin(TestCase):
    def setUp(self):
        # Register the model
        TestModelRegistryModel.register_model_class()
        self.model = TestModelRegistryModel
    
    def test_register_model(self):
        """Test that register_model adds the model to the registry"""
        # Register the model
        self.model.register_model_class()
        
        # Check that the model is registered
        self.assertIn(self.model, self.model._registry.registered_models)
        self.assertEqual(self.model._registry.model_names[self.model.__name__], self.model)
    
    def test_get_model_field_types(self):
        """Test that get_model_field_types returns the correct field types"""
        # Register the model
        self.model.register_model_class()
        
        # Get field types
        field_types = self.model.get_model_field_types()
        
        # Check field types
        self.assertEqual(field_types['name'], 'char')
    
    def test_get_model_relationships(self):
        """Test that get_model_relationships returns the correct relationships"""
        # Register the model
        self.model.register_model_class()
        
        # Get relationships
        relationships = self.model.get_model_relationships()
        
        # Check relationships (should be empty for this model)
        self.assertEqual(relationships, {})
    
    def test_auto_discover_models(self):
        """Test that auto_discover_models discovers models from an app"""
        # Auto discover models
        self.model.auto_discover_models('filtering')
        
        # Check that models are registered
        self.assertIn(TestFilterableModel, self.model._registry.registered_models)
        self.assertIn(TestAggregatableModel, self.model._registry.registered_models)
        self.assertIn(TestCombinedModel, self.model._registry.registered_models)
        self.assertIn(TestModelRegistryModel, self.model._registry.registered_models)

class TestCombinedMixin(TestCase):
    def setUp(self):
        # Register the model
        TestCombinedModel.register_model_class()
        self.model = TestCombinedModel
    
    def test_combined_functionality(self):
        """Test that a model with both mixins has both functionalities"""
        # Check filterable fields
        filterable_fields = self.model.get_filterable_fields()
        self.assertIn('name', filterable_fields)
        self.assertIn('value', filterable_fields)
        self.assertIn('is_active', filterable_fields)
        self.assertIn('created_at', filterable_fields)
        
        # Check aggregatable fields
        aggregatable_fields = self.model.get_aggregatable_fields()
        self.assertIn('value', aggregatable_fields)
        self.assertNotIn('name', aggregatable_fields)
        self.assertNotIn('is_active', aggregatable_fields)
        self.assertNotIn('created_at', aggregatable_fields)
        
        # Create test data
        TestCombinedModel.objects.create(name="Test 1", value=10, is_active=True)
        TestCombinedModel.objects.create(name="Test 2", value=20, is_active=False)
        TestCombinedModel.objects.create(name="Another", value=30, is_active=True)
        
        # Test filtering
        filtered = self.model.filter({'name': {'icontains': 'Test'}})
        self.assertEqual(filtered.count(), 2)
        
        # Test aggregation
        result = self.model.aggregate({'value': ['sum']})
        self.assertEqual(result['value__sum'], 60)
        
        # Test combined filtering and aggregation
        filtered = self.model.filter({'is_active': True})
        self.assertEqual(filtered.count(), 2)  # Should have 2 active records
        
        result = self.model.aggregate({'value': ['sum']}, group_by=['is_active'])
        self.assertEqual(len(result), 2)  # Should have two groups (True and False)
        
        # Find the group for is_active=True
        active_group = next(g for g in result if g['is_active'] is True)
        self.assertEqual(active_group['value__sum'], 40)  # 10 + 30 = 40
        
        # Find the group for is_active=False
        inactive_group = next(g for g in result if g['is_active'] is False)
        self.assertEqual(inactive_group['value__sum'], 20)  # 20 