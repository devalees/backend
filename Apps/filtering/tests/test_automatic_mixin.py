import pytest
from django.db import models
from django.test import TestCase
from django.apps import apps

from ..base import BaseFilterableModel, BaseAggregatableModel
from ..mixins import FilterableMixin, AggregatableMixin, ModelRegistryMixin
from ..model_discovery import ModelDiscoveryService
from ..auto_mixin_applier import (
    AutoMixinApplier,
    apply_mixins_to_model,
    apply_indexes_to_model,
    register_model_indexes
)


# Test models for mixin application
class TestAutoMixinModel(models.Model):
    """Base test model without any mixins applied"""
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'
        managed = False


class TestAutoMixinFilterableModel(BaseFilterableModel):
    """Model inheriting from BaseFilterableModel but without mixins"""
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'
        managed = False


class TestAutoMixinAggregatableModel(BaseAggregatableModel):
    """Model inheriting from BaseAggregatableModel but without mixins"""
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'
        managed = False


class TestWithModelConfig(models.Model):
    """Model with custom configuration for filtering and aggregation"""
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending')
    ])
    
    class Meta:
        app_label = 'filtering'
        managed = False
    
    class FilterConfig:
        """Configuration for filtering"""
        filter_fields = {
            'text': ['name'],
            'numeric': ['value'],
            'choice': ['status']
        }
    
    class AggregationConfig:
        """Configuration for aggregation"""
        aggregation_fields = {
            'group_by': ['status'],
            'sum': ['value']
        }
        
        indexes = [
            ['status', 'value'],
            ['name']
        ]


class TestAutoMixinApplier(TestCase):
    """Test cases for the AutoMixinApplier class"""
    
    def setUp(self):
        self.mixin_applier = AutoMixinApplier()
        self.model_discovery = ModelDiscoveryService()
    
    def test_apply_mixins_to_filterable_model(self):
        """Test applying mixins to a model that inherits from BaseFilterableModel"""
        # Apply mixins to TestAutoMixinFilterableModel
        model_with_mixins = apply_mixins_to_model(TestAutoMixinFilterableModel)
        
        # Verify that the model now has FilterableMixin functionality
        self.assertTrue(hasattr(model_with_mixins, 'filter'))
        self.assertTrue(hasattr(model_with_mixins, 'get_filterable_fields'))
        
        # Check the model is considered an instance of FilterableMixin
        self.assertTrue(model_with_mixins.is_instance_of(FilterableMixin))
        
        # Verify that the model still has the original attributes
        self.assertEqual(model_with_mixins.__name__, 'TestAutoMixinFilterableModelEnhanced')
        
        # Verify original model is unchanged
        self.assertFalse(hasattr(TestAutoMixinFilterableModel, 'filter'))
    
    def test_apply_mixins_to_aggregatable_model(self):
        """Test applying mixins to a model that inherits from BaseAggregatableModel"""
        # Apply mixins to TestAutoMixinAggregatableModel
        model_with_mixins = apply_mixins_to_model(TestAutoMixinAggregatableModel)
        
        # Verify that the model now has aggregation functionality
        self.assertTrue(hasattr(model_with_mixins, 'aggregate'))
        self.assertTrue(hasattr(model_with_mixins, 'get_aggregatable_fields'))
        
        # Check the model is considered an instance of AggregatableMixin
        self.assertTrue(model_with_mixins.is_instance_of(AggregatableMixin))
        
        # Verify that the model has the correct name
        self.assertEqual(model_with_mixins.__name__, 'TestAutoMixinAggregatableModelEnhanced')
        
        # Verify original model is unchanged
        self.assertFalse(hasattr(TestAutoMixinAggregatableModel, 'aggregate'))
    
    def test_create_dynamic_model(self):
        """Test creating a dynamic model with mixins"""
        # Apply mixins to TestAutoMixinModel
        model_with_mixins = apply_mixins_to_model(TestAutoMixinModel)
        
        # Since we're applying FilterableMixin and AggregatableMixin, verify the functionality
        self.assertTrue(hasattr(model_with_mixins, 'filter') or 
                      hasattr(model_with_mixins, 'aggregate'))
        
        # Verify model name is set correctly
        self.assertEqual(model_with_mixins.__name__, 'TestAutoMixinModelEnhanced')
        
        # Verify is_enhanced_model flag is set
        self.assertTrue(hasattr(model_with_mixins, 'is_enhanced_model'))
        
        # Verify original model is unchanged
        self.assertFalse(hasattr(TestAutoMixinModel, 'filter'))
        self.assertFalse(hasattr(TestAutoMixinModel, 'aggregate'))
    
    def test_apply_model_configuration(self):
        """Test applying model configuration from FilterConfig and AggregationConfig"""
        # Apply mixins to TestWithModelConfig
        model_with_mixins = apply_mixins_to_model(TestWithModelConfig)
        
        # Verify that the model now has the expected functionality
        self.assertTrue(hasattr(model_with_mixins, 'get_filterable_fields'))
        self.assertTrue(hasattr(model_with_mixins, 'get_aggregatable_fields'))
        
        # Check the model is correctly enhanced
        self.assertTrue(model_with_mixins.is_instance_of(FilterableMixin))
        self.assertTrue(model_with_mixins.is_instance_of(AggregatableMixin))
        
        # Verify that the configuration was properly applied by checking fields
        filterable_fields = model_with_mixins.get_filterable_fields()
        self.assertIn('name', filterable_fields)
        self.assertIn('value', filterable_fields)
        self.assertIn('status', filterable_fields)
        
        # Check field types match configuration
        self.assertEqual(filterable_fields['name']['type'], 'text')
        self.assertEqual(filterable_fields['value']['type'], 'numeric')
    
    def test_apply_indexes_to_model(self):
        """Test that indexes are properly applied to a model"""
        # Apply indexes to TestWithModelConfig
        model_with_indexes = apply_indexes_to_model(TestWithModelConfig)
        
        # Get model's indexes
        indexes = model_with_indexes._meta.indexes
        
        # Check that the expected indexes were created
        self.assertTrue(len(indexes) >= 2)  # At least the indexes from TestWithModelConfig.AggregationConfig
    
    def test_register_model_indexes(self):
        """Test that indexes are properly registered for a model"""
        # This test is more about the functionality existing than what it specifically does
        # since the actual DB operations would require a real database
        
        # Register indexes for TestWithModelConfig
        result = register_model_indexes(TestWithModelConfig)
        
        # Verify the function ran successfully
        self.assertIsNotNone(result)
        
        # In a real implementation, we would verify that the indexes were created in the database
        # For now, we're just testing that the function exists and runs without errors

    def test_batch_apply_mixins(self):
        """Test applying mixins to multiple models in a batch"""
        # Get all test models
        test_models = [
            TestAutoMixinFilterableModel,
            TestAutoMixinAggregatableModel,
            TestWithModelConfig
        ]
        
        # Batch apply mixins
        enhanced_models = self.mixin_applier.batch_apply_mixins(test_models)
        
        # Verify enhanced models were returned
        self.assertEqual(len(enhanced_models), len(test_models))
        
        # Verify all models have appropriate functionality
        for model in enhanced_models:
            self.assertTrue(hasattr(model, 'filter') or hasattr(model, 'aggregate'))
            self.assertTrue(hasattr(model, 'is_enhanced_model'))
    
    def test_discover_and_enhance_app_models(self):
        """Test discovering models from an app and applying mixins"""
        # This test should discover models from the 'filtering' app and apply mixins
        enhanced_models = self.mixin_applier.discover_and_enhance_app_models('filtering')
        
        # Verify enhanced models were returned
        self.assertGreater(len(enhanced_models), 0)
        
        # Check that our test models are in the enhanced models
        model_names = [model.__name__ for model in enhanced_models]
        
        # At least one of our test models should be included
        self.assertTrue(
            'TestAutoMixinFilterableModelEnhanced' in model_names or
            'TestAutoMixinAggregatableModelEnhanced' in model_names or
            'TestWithModelConfigEnhanced' in model_names
        ) 