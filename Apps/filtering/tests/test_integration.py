import pytest
from django.db import models
from django.test import TestCase
from unittest.mock import patch, MagicMock

from ..model_config import ModelConfig
from ..model_registry import ModelRegistry, model_registry
from ..base_model import FilterableModel, AggregatableModel, FilterableAggregatableModel


class IntegrationTestCase(TestCase):
    """Integration tests for filtering and aggregation system."""
    
    def test_model_inheritance_and_registration(self):
        """Test that model inheritance and registration work together."""
        # Create a model that inherits from FilterableModel with a unique name
        class TestIntegrationFilterableModel(FilterableModel):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'filtering'
                # Use abstract = True to avoid conflicts
                abstract = True
            
            class FilterConfig:
                text = ['name']
        
        # Manually register with the model registry
        config = model_registry.register(TestIntegrationFilterableModel)
        
        # Check that its configuration was created correctly
        assert config is not None
        assert config.model_class == TestIntegrationFilterableModel
        assert 'name' in config.get_filter_fields('text')
    
    def test_aggregatable_model_integration(self):
        """Test integration with AggregatableModel."""
        # Create a model that inherits from AggregatableModel with a unique name
        class TestIntegrationAggregatableModel(AggregatableModel):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                # Use abstract = True to avoid conflicts
                abstract = True
            
            class AggregationConfig:
                sum = ['amount']
        
        # Manually register with the model registry
        config = model_registry.register(TestIntegrationAggregatableModel)
        
        # Check that its configuration was created correctly
        assert config is not None
        assert config.model_class == TestIntegrationAggregatableModel
        assert 'amount' in config.get_aggregation_fields('sum')
    
    def test_filterable_aggregatable_model_integration(self):
        """Test integration with FilterableAggregatableModel."""
        # Create a model that inherits from FilterableAggregatableModel with a unique name
        class TestIntegrationCombinedModel(FilterableAggregatableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                # Use abstract = True to avoid conflicts
                abstract = True
            
            class FilterConfig:
                text = ['name']
                
            class AggregationConfig:
                sum = ['amount']
        
        # Manually register with the model registry
        config = model_registry.register(TestIntegrationCombinedModel)
        
        # Check that its configuration was created correctly
        assert config is not None
        assert config.model_class == TestIntegrationCombinedModel
        assert 'name' in config.get_filter_fields('text')
        assert 'amount' in config.get_aggregation_fields('sum')
    
    def test_discover_and_register_models(self):
        """Test discovering and registering models."""
        # Create a temporary registry
        temp_registry = ModelRegistry()
        
        # Create some models that will be discovered
        class IntegrationTestModel1(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
        
        class IntegrationTestModel2(models.Model):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
        
        # Mock discovering the models
        temp_registry._discovered_models.add(IntegrationTestModel1)
        temp_registry._discovered_models.add(IntegrationTestModel2)
        
        # Register discovered models
        temp_registry.register_discovered_models()
        
        # Check that they were registered
        assert temp_registry.is_registered(IntegrationTestModel1)
        assert temp_registry.is_registered(IntegrationTestModel2)
        
        # Check that configs were created
        assert temp_registry.get_config(IntegrationTestModel1) is not None
        assert temp_registry.get_config(IntegrationTestModel2) is not None


class TestEndToEndUsage:
    """End-to-end tests for typical usage of the filtering system."""
    
    @pytest.fixture
    def setup_model(self):
        """Fixture to set up a model for testing."""
        # Create a model with a unique name
        class TestIntegrationEndToEndModel(FilterableAggregatableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            is_active = models.BooleanField(default=True)
            created_at = models.DateTimeField(auto_now_add=True)
            
            class Meta:
                app_label = 'filtering'
                abstract = True  # Make abstract for testing
            
            class FilterConfig:
                text = ['name']
                numeric = ['amount']
                boolean = ['is_active']
                date = ['created_at']
                
            class AggregationConfig:
                group_by = ['is_active']
                sum = ['amount']
                
        return TestIntegrationEndToEndModel
    
    def test_model_definition_with_configs(self, setup_model):
        """Test that model definition with configs works correctly."""
        TestModel = setup_model
        
        # Check that FilterConfig is accessible
        assert hasattr(TestModel, 'FilterConfig')
        assert TestModel.FilterConfig.text == ['name']
        
        # Check that AggregationConfig is accessible
        assert hasattr(TestModel, 'AggregationConfig')
        assert TestModel.AggregationConfig.sum == ['amount']
    
    def test_config_creation_from_model(self, setup_model):
        """Test creating a configuration from a model."""
        TestModel = setup_model
        
        # Create a config for the model
        config = ModelConfig(TestModel)
        
        # Check that filter fields were loaded correctly
        assert 'name' in config.filter_fields['text']
        assert 'amount' in config.filter_fields['numeric']
        assert 'is_active' in config.filter_fields['boolean']
        assert 'created_at' in config.filter_fields['date']
        
        # Check that aggregation fields were loaded correctly
        assert 'is_active' in config.aggregation_fields['group_by']
        assert 'amount' in config.aggregation_fields['sum'] 