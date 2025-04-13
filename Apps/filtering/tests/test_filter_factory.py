import pytest
from django.db import models
from django.test import TestCase
from django.db.models import Q
from typing import Dict, Any, Callable

from ..base import BaseFilterableModel, BaseFilterRegistry
from ..filter_factory import (
    FilterFactory,
    BasicFilterFactory,
    AdvancedFilterFactory,
    FilterTypeMapping
)
from ..models import TestFilterableModel

class TestFilterFactory(TestCase):
    """Test cases for the FilterFactory class"""
    
    def setUp(self):
        """Set up test environment"""
        self.filter_factory = FilterFactory()
        self.basic_filter_factory = BasicFilterFactory()
        self.advanced_filter_factory = AdvancedFilterFactory()
        self.filter_type_mapping = FilterTypeMapping()
        
        # Register the model
        TestFilterableModel.register_model_class()
    
    def test_basic_filter_factory_creation(self):
        """Test that BasicFilterFactory creates filters correctly"""
        # Create a filter for a text field
        text_filter = self.basic_filter_factory.create_filter('name', 'Test')
        self.assertIsInstance(text_filter, Q)
        
        # Create a filter for a numeric field
        numeric_filter = self.basic_filter_factory.create_filter('age', 25)
        self.assertIsInstance(numeric_filter, Q)
        
        # Create a filter for a boolean field
        boolean_filter = self.basic_filter_factory.create_filter('is_active', True)
        self.assertIsInstance(boolean_filter, Q)
    
    def test_advanced_filter_factory_creation(self):
        """Test that AdvancedFilterFactory creates filters correctly"""
        # Create a filter with an operator
        text_filter = self.advanced_filter_factory.create_filter('name', {'startswith': 'Test'})
        self.assertIsInstance(text_filter, Q)
        
        # Create a filter with multiple operators
        complex_filter = self.advanced_filter_factory.create_filter('age', {
            'gte': 20,
            'lte': 30
        })
        self.assertIsInstance(complex_filter, Q)
    
    def test_filter_type_mapping(self):
        """Test that FilterTypeMapping maps field types to filter factories correctly"""
        # Get the filter factory for a text field
        text_factory = self.filter_type_mapping.get_filter_factory('char')
        self.assertEqual(text_factory, self.basic_filter_factory)
        
        # Get the filter factory for a numeric field
        numeric_factory = self.filter_type_mapping.get_filter_factory('integer')
        self.assertEqual(numeric_factory, self.basic_filter_factory)
        
        # Get the filter factory for an advanced filter
        advanced_factory = self.filter_type_mapping.get_filter_factory('advanced')
        self.assertEqual(advanced_factory, self.advanced_filter_factory)
    
    def test_filter_factory_integration(self):
        """Test that FilterFactory integrates with the model correctly"""
        # Create a filter for a model field
        filter_obj = self.filter_factory.create_filter_for_field(
            TestFilterableModel, 'name', 'Test'
        )
        self.assertIsInstance(filter_obj, Q)
        
        # Create a filter with an operator
        filter_obj = self.filter_factory.create_filter_for_field(
            TestFilterableModel, 'name', {'startswith': 'Test'}
        )
        self.assertIsInstance(filter_obj, Q)
    
    def test_filter_factory_with_invalid_field(self):
        """Test that FilterFactory raises an error for invalid fields"""
        with self.assertRaises(ValueError):
            self.filter_factory.create_filter_for_field(
                TestFilterableModel, 'invalid_field', 'value'
            )
    
    def test_filter_factory_with_invalid_operator(self):
        """Test that FilterFactory raises an error for invalid operators"""
        with self.assertRaises(ValueError):
            self.filter_factory.create_filter_for_field(
                TestFilterableModel, 'name', {'invalid_operator': 'value'}
            )
    
    def test_filter_factory_with_invalid_type(self):
        """Test that FilterFactory raises an error for invalid field types"""
        # Create a model with an invalid field type
        class InvalidModel(BaseFilterableModel):
            name = models.CharField(max_length=100)
            
            @classmethod
            def get_filterable_fields(cls):
                return {'name': {'type': 'invalid_type'}}
        
        with self.assertRaises(ValueError):
            self.filter_factory.create_filter_for_field(
                InvalidModel, 'name', 'value'
            )
    
    def test_filter_factory_with_custom_filter(self):
        """Test that FilterFactory supports custom filters"""
        # Register a custom filter
        def custom_filter(field, value):
            return Q(**{f"{field}__custom": value})
        
        self.filter_factory.register_custom_filter('custom', custom_filter)
        
        # Create a filter with the custom filter
        filter_obj = self.filter_factory.create_filter_for_field(
            TestFilterableModel, 'name', {'custom': 'value'}
        )
        self.assertIsInstance(filter_obj, Q) 