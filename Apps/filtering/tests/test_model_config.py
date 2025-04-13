import pytest
from django.db import models
from django.test import TestCase

from ..model_config import ModelConfig


class TestModelConfigClass:
    """Test suite for the ModelConfig class."""

    class TestModel(models.Model):
        """Test model for configuration testing."""
        name = models.CharField(max_length=100)
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        created_at = models.DateTimeField(auto_now_add=True)
        is_active = models.BooleanField(default=True)
        
        class Meta:
            app_label = 'filtering'
            abstract = True

    class TestModelWithConfig(models.Model):
        """Test model with configuration classes defined."""
        name = models.CharField(max_length=100)
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        created_at = models.DateTimeField(auto_now_add=True)
        is_active = models.BooleanField(default=True)
        
        class Meta:
            app_label = 'filtering'
            abstract = True
            
        class FilterConfig:
            text = ['name']
            numeric = ['amount']
            date = ['created_at']
            boolean = ['is_active']
            indexes = [['created_at'], ['name', 'is_active']]
            
        class AggregationConfig:
            group_by = ['is_active']
            sum = ['amount']
            count = ['id']

    def test_create_model_config(self):
        """Test creating a ModelConfig instance."""
        config = ModelConfig(self.TestModel)
        
        assert config is not None
        assert config.model_class == self.TestModel
        assert config.model_name == 'TestModel'
        
    def test_empty_config_by_default(self):
        """Test that a model without config classes has empty configurations."""
        config = ModelConfig(self.TestModel)
        
        # Check filter fields
        assert all(len(fields) == 0 for fields in config.filter_fields.values())
        
        # Check aggregation fields
        assert all(len(fields) == 0 for fields in config.aggregation_fields.values())
        
        # Check indexes
        assert len(config.indexes) == 0
        
    def test_load_config_from_model(self):
        """Test loading configuration from a model with config classes."""
        config = ModelConfig(self.TestModelWithConfig)
        
        # Check filter fields
        assert 'name' in config.filter_fields['text']
        assert 'amount' in config.filter_fields['numeric']
        assert 'created_at' in config.filter_fields['date']
        assert 'is_active' in config.filter_fields['boolean']
        
        # Check aggregation fields
        assert 'is_active' in config.aggregation_fields['group_by']
        assert 'amount' in config.aggregation_fields['sum']
        assert 'id' in config.aggregation_fields['count']
        
        # Check indexes
        assert ['created_at'] in config.indexes
        assert ['name', 'is_active'] in config.indexes
        
    def test_get_filter_fields(self):
        """Test getting filter fields."""
        config = ModelConfig(self.TestModelWithConfig)
        
        # Get all filter fields
        all_fields = config.get_filter_fields()
        assert isinstance(all_fields, dict)
        assert len(all_fields) > 0
        
        # Get specific filter field type
        text_fields = config.get_filter_fields('text')
        assert isinstance(text_fields, list)
        assert 'name' in text_fields
        
        # Get non-existent filter field type
        non_existent = config.get_filter_fields('non_existent')
        assert isinstance(non_existent, list)
        assert len(non_existent) == 0
        
    def test_get_aggregation_fields(self):
        """Test getting aggregation fields."""
        config = ModelConfig(self.TestModelWithConfig)
        
        # Get all aggregation fields
        all_fields = config.get_aggregation_fields()
        assert isinstance(all_fields, dict)
        assert len(all_fields) > 0
        
        # Get specific aggregation field type
        sum_fields = config.get_aggregation_fields('sum')
        assert isinstance(sum_fields, list)
        assert 'amount' in sum_fields
        
        # Get non-existent aggregation field type
        non_existent = config.get_aggregation_fields('non_existent')
        assert isinstance(non_existent, list)
        assert len(non_existent) == 0
        
    def test_get_indexes(self):
        """Test getting indexes."""
        config = ModelConfig(self.TestModelWithConfig)
        
        indexes = config.get_indexes()
        assert isinstance(indexes, list)
        assert len(indexes) == 2
        assert ['created_at'] in indexes
        assert ['name', 'is_active'] in indexes
        
    def test_create_for_model_factory_method(self):
        """Test the create_for_model factory method."""
        config = ModelConfig.create_for_model(self.TestModelWithConfig)
        
        assert isinstance(config, ModelConfig)
        assert config.model_class == self.TestModelWithConfig
        assert config.model_name == 'TestModelWithConfig' 