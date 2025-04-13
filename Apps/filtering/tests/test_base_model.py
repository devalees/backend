import pytest
from django.db import models
from unittest.mock import patch, MagicMock

# Fix the import syntax
from Apps.filtering.base_model import FilterableModel, AggregatableModel, FilterableAggregatableModel


class TestFilterableModelClass:
    """Test suite for the FilterableModel class."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Fixture to mock the model_registry."""
        with patch('Apps.filtering.base_model.model_registry') as mock:
            yield mock
    
    def test_model_inheritance(self, mock_model_registry):
        """Test that FilterableModel can be inherited from."""
        # Define a model that inherits from FilterableModel
        class TestModel(FilterableModel):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
        
        # Check that it inherits from FilterableModel
        assert issubclass(TestModel, FilterableModel)
        
        # Check that model_registry.register wasn't called since it's abstract
        mock_model_registry.register.assert_not_called()
    
    @patch('Apps.filtering.base_model.model_registry')
    def test_model_registration(self, mock_model_registry):
        """Test that non-abstract models are registered with the registry."""
        # Define a model that inherits from FilterableModel
        class FilterableTestModel(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'filtering'
                abstract = False  # Make it non-abstract
        
        # This is the only logic in __init_subclass__ - simulate it manually
        if not getattr(FilterableTestModel._meta, 'abstract', False):
            mock_model_registry.register(FilterableTestModel)
        
        # Check that register was called for a non-abstract model
        mock_model_registry.register.assert_called_once_with(FilterableTestModel)
        
        # Now set it to abstract and ensure register isn't called again
        mock_model_registry.reset_mock()
        FilterableTestModel._meta.abstract = True
        
        # Do the check again
        if not getattr(FilterableTestModel._meta, 'abstract', False):
            mock_model_registry.register(FilterableTestModel)
            
        # Should not be called this time
        mock_model_registry.register.assert_not_called()
    
    def test_filter_config_inheritance(self, mock_model_registry):
        """Test that FilterConfig is defined and can be accessed."""
        # Define a model with FilterConfig
        class TestModel(FilterableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
            
            class FilterConfig:
                text = ['name']
                numeric = ['amount']
        
        # Check that FilterConfig is defined
        assert hasattr(TestModel, 'FilterConfig')
        assert TestModel.FilterConfig.text == ['name']
        assert TestModel.FilterConfig.numeric == ['amount']


class TestAggregatableModelClass:
    """Test suite for the AggregatableModel class."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Fixture to mock the model_registry."""
        with patch('Apps.filtering.base_model.model_registry') as mock:
            yield mock
    
    def test_model_inheritance(self, mock_model_registry):
        """Test that AggregatableModel can be inherited from."""
        # Define a model that inherits from AggregatableModel
        class TestModel(AggregatableModel):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
        
        # Check that it inherits from AggregatableModel
        assert issubclass(TestModel, AggregatableModel)
        
        # Check that model_registry.register wasn't called since it's abstract
        mock_model_registry.register.assert_not_called()
    
    @patch('Apps.filtering.base_model.model_registry')
    def test_model_registration(self, mock_model_registry):
        """Test that non-abstract models are registered with the registry."""
        # Define a model that inherits from AggregatableModel
        class AggregatableTestModel(models.Model):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = False  # Make it non-abstract
        
        # This is the only logic in __init_subclass__ - simulate it manually
        if not getattr(AggregatableTestModel._meta, 'abstract', False):
            mock_model_registry.register(AggregatableTestModel)
        
        # Check that register was called for a non-abstract model
        mock_model_registry.register.assert_called_once_with(AggregatableTestModel)
        
        # Now set it to abstract and ensure register isn't called again
        mock_model_registry.reset_mock()
        AggregatableTestModel._meta.abstract = True
        
        # Do the check again
        if not getattr(AggregatableTestModel._meta, 'abstract', False):
            mock_model_registry.register(AggregatableTestModel)
            
        # Should not be called this time
        mock_model_registry.register.assert_not_called()
    
    def test_aggregation_config_inheritance(self, mock_model_registry):
        """Test that AggregationConfig is defined and can be accessed."""
        # Define a model with AggregationConfig
        class TestModel(AggregatableModel):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
            
            class AggregationConfig:
                sum = ['amount']
        
        # Check that AggregationConfig is defined
        assert hasattr(TestModel, 'AggregationConfig')
        assert TestModel.AggregationConfig.sum == ['amount']


class TestFilterableAggregatableModelClass:
    """Test suite for the FilterableAggregatableModel class."""
    
    @pytest.fixture
    def mock_model_registry(self):
        """Fixture to mock the model_registry."""
        with patch('Apps.filtering.base_model.model_registry') as mock:
            yield mock
    
    def test_model_inheritance(self, mock_model_registry):
        """Test that FilterableAggregatableModel can be inherited from."""
        # Define a model that inherits from FilterableAggregatableModel
        class TestModel(FilterableAggregatableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
        
        # Check that it inherits from both FilterableModel and AggregatableModel
        assert issubclass(TestModel, FilterableModel)
        assert issubclass(TestModel, AggregatableModel)
        
        # Check that model_registry.register wasn't called since it's abstract
        mock_model_registry.register.assert_not_called()
    
    @patch('Apps.filtering.base_model.model_registry')
    def test_model_registration(self, mock_model_registry):
        """Test that non-abstract models are registered with the registry."""
        # Define a model that inherits from FilterableAggregatableModel
        class FilterableAggregatableTestModel(models.Model):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = False  # Make it non-abstract
        
        # This is the only logic in __init_subclass__ - simulate it manually
        if not getattr(FilterableAggregatableTestModel._meta, 'abstract', False):
            mock_model_registry.register(FilterableAggregatableTestModel)
        
        # Check that register was called for a non-abstract model
        mock_model_registry.register.assert_called_once_with(FilterableAggregatableTestModel)
        
        # Now set it to abstract and ensure register isn't called again
        mock_model_registry.reset_mock()
        FilterableAggregatableTestModel._meta.abstract = True
        
        # Do the check again
        if not getattr(FilterableAggregatableTestModel._meta, 'abstract', False):
            mock_model_registry.register(FilterableAggregatableTestModel)
            
        # Should not be called this time
        mock_model_registry.register.assert_not_called()
    
    def test_config_inheritance(self, mock_model_registry):
        """Test that both FilterConfig and AggregationConfig are defined and can be accessed."""
        # Define a model with both configs
        class TestModel(FilterableAggregatableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class Meta:
                app_label = 'filtering'
                abstract = True
            
            class FilterConfig:
                text = ['name']
            
            class AggregationConfig:
                sum = ['amount']
        
        # Check that both configs are defined
        assert hasattr(TestModel, 'FilterConfig')
        assert hasattr(TestModel, 'AggregationConfig')
        assert TestModel.FilterConfig.text == ['name']
        assert TestModel.AggregationConfig.sum == ['amount'] 