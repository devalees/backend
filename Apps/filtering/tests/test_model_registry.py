import pytest
from django.db import models
from django.test import TestCase
from django.apps import apps
from ..base import (
    BaseFilterableModel,
    BaseAggregatableModel,
    BaseFilterRegistry,
    BaseAggregationRegistry
)
from ..registry import ModelRegistry

class RegistryTestModel(BaseFilterableModel, BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'

class TestModelRegistry(TestCase):
    def setUp(self):
        self.registry = ModelRegistry()
        self.test_model = RegistryTestModel

    def test_register_model(self):
        """Test registering a model with the registry"""
        self.registry.register_model(self.test_model)
        assert self.test_model in self.registry.registered_models
        assert self.test_model.__name__ in self.registry.model_names

    def test_register_model_duplicate(self):
        """Test registering the same model twice doesn't cause issues"""
        self.registry.register_model(self.test_model)
        self.registry.register_model(self.test_model)
        assert self.test_model in self.registry.registered_models
        assert len(self.registry.registered_models) == 1

    def test_get_model_by_name(self):
        """Test retrieving a model by name"""
        self.registry.register_model(self.test_model)
        retrieved_model = self.registry.get_model_by_name(self.test_model.__name__)
        assert retrieved_model == self.test_model

    def test_get_model_by_name_nonexistent(self):
        """Test retrieving a non-existent model by name raises KeyError"""
        with pytest.raises(KeyError):
            self.registry.get_model_by_name('NonexistentModel')

    def test_get_model_field_types(self):
        """Test retrieving field types for a model"""
        self.registry.register_model(self.test_model)
        field_types = self.registry.get_model_field_types(self.test_model)
        assert isinstance(field_types, dict)
        assert 'name' in field_types
        assert 'value' in field_types
        assert field_types['name'] == 'char'
        assert field_types['value'] == 'integer'

    def test_get_model_relationships(self):
        """Test retrieving relationships for a model"""
        self.registry.register_model(self.test_model)
        relationships = self.registry.get_model_relationships(self.test_model)
        assert isinstance(relationships, dict)
        # This model has no relationships, so the dict should be empty
        assert len(relationships) == 0

class TestModelWithRelationships(BaseFilterableModel, BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    related = models.ForeignKey(RegistryTestModel, on_delete=models.CASCADE, related_name='related_items')
    
    class Meta:
        app_label = 'filtering'

class TestModelRegistryWithRelationships(TestCase):
    def setUp(self):
        self.registry = ModelRegistry()
        self.test_model = RegistryTestModel
        self.related_model = TestModelWithRelationships
        self.registry.register_model(self.test_model)
        self.registry.register_model(self.related_model)

    def test_get_model_relationships(self):
        """Test retrieving relationships for a model with relationships"""
        relationships = self.registry.get_model_relationships(self.related_model)
        assert isinstance(relationships, dict)
        assert 'related' in relationships
        assert relationships['related']['type'] == 'foreignkey'
        assert relationships['related']['model'] == self.test_model

    def test_auto_discover_models(self):
        """Test auto-discovering models in the app"""
        # Clear the registry
        self.registry.registered_models = set()
        self.registry.model_names = {}
        
        # Auto-discover models
        self.registry.auto_discover_models('filtering')
        
        # Check that our test models were discovered
        assert self.test_model in self.registry.registered_models
        assert self.related_model in self.registry.registered_models 