import pytest
from django.db import models
from django.test import TestCase
from ..base import (
    BaseFilterableModel,
    BaseAggregatableModel,
    BaseFilterRegistry,
    BaseAggregationRegistry
)

class TestModel(BaseFilterableModel, BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'

class TestBaseFilterableModel(TestCase):
    def setUp(self):
        self.model = TestModel

    def test_model_inheritance(self):
        """Test that the model properly inherits from BaseFilterableModel"""
        assert issubclass(self.model, BaseFilterableModel)
        assert hasattr(self.model, 'get_filterable_fields')

    def test_get_filterable_fields(self):
        """Test that get_filterable_fields returns correct field information"""
        fields = self.model.get_filterable_fields()
        assert isinstance(fields, dict)
        assert 'name' in fields
        assert 'value' in fields
        assert fields['name']['type'] == 'char'
        assert fields['value']['type'] == 'integer'

class TestBaseAggregatableModel(TestCase):
    def setUp(self):
        self.model = TestModel

    def test_model_inheritance(self):
        """Test that the model properly inherits from BaseAggregatableModel"""
        assert issubclass(self.model, BaseAggregatableModel)
        assert hasattr(self.model, 'get_aggregatable_fields')

    def test_get_aggregatable_fields(self):
        """Test that get_aggregatable_fields returns correct field information"""
        fields = self.model.get_aggregatable_fields()
        assert isinstance(fields, dict)
        assert 'value' in fields
        assert fields['value']['type'] == 'integer'

class TestBaseFilterRegistry(TestCase):
    def setUp(self):
        self.registry = BaseFilterRegistry()

    def test_register_filter(self):
        """Test registering a new filter type"""
        def test_filter(field, value):
            return models.Q(**{field: value})
        
        self.registry.register('test', test_filter)
        assert 'test' in self.registry.filters
        assert callable(self.registry.filters['test'])

    def test_get_filter(self):
        """Test retrieving a registered filter"""
        def test_filter(field, value):
            return models.Q(**{field: value})
        
        self.registry.register('test', test_filter)
        retrieved_filter = self.registry.get_filter('test')
        assert callable(retrieved_filter)
        assert retrieved_filter == test_filter

    def test_get_nonexistent_filter(self):
        """Test retrieving a non-existent filter raises KeyError"""
        with pytest.raises(KeyError):
            self.registry.get_filter('nonexistent')

class TestBaseAggregationRegistry(TestCase):
    def setUp(self):
        self.registry = BaseAggregationRegistry()

    def test_register_aggregation(self):
        """Test registering a new aggregation type"""
        def test_aggregation(field):
            return models.Count(field)
        
        self.registry.register('test', test_aggregation)
        assert 'test' in self.registry.aggregations
        assert callable(self.registry.aggregations['test'])

    def test_get_aggregation(self):
        """Test retrieving a registered aggregation"""
        def test_aggregation(field):
            return models.Count(field)
        
        self.registry.register('test', test_aggregation)
        retrieved_aggregation = self.registry.get_aggregation('test')
        assert callable(retrieved_aggregation)
        assert retrieved_aggregation == test_aggregation

    def test_get_nonexistent_aggregation(self):
        """Test retrieving a non-existent aggregation raises KeyError"""
        with pytest.raises(KeyError):
            self.registry.get_aggregation('nonexistent') 