import pytest
from django.db import models
from django.test import TestCase, override_settings
from django.apps import apps

from ..base import BaseFilterableModel, BaseAggregatableModel
from ..model_discovery import ModelDiscoveryService
from django.conf import settings


class TestModelA(BaseFilterableModel, BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'filtering'


class TestModelB(BaseFilterableModel, BaseAggregatableModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    model_a = models.ForeignKey(TestModelA, on_delete=models.CASCADE, related_name='related_bs')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering'


class TestModelC(models.Model):
    """Not inheriting from base filterable/aggregatable models"""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'filtering'


class TestModelD(BaseFilterableModel):
    """Only inheriting from filterable model"""
    name = models.CharField(max_length=100)
    relation_many = models.ManyToManyField(TestModelA, related_name='related_ds')
    
    class Meta:
        app_label = 'filtering'


class TestModelE(BaseAggregatableModel):
    """Only inheriting from aggregatable model"""
    name = models.CharField(max_length=100)
    related_one = models.OneToOneField(TestModelA, on_delete=models.CASCADE, related_name='related_e')
    
    class Meta:
        app_label = 'filtering'


class TestModelDiscovery(TestCase):
    def setUp(self):
        self.discovery_service = ModelDiscoveryService()

    def test_discover_models_from_app(self):
        """Test discovering models from a specific app"""
        discovered_models = self.discovery_service.discover_models_from_app('filtering')
        
        model_names = [model.__name__ for model in discovered_models]
        
        # Check if our test models are discovered
        assert 'TestModelA' in model_names
        assert 'TestModelB' in model_names
        # TestModelC should not be discovered because it doesn't inherit from base models
        assert 'TestModelC' not in model_names
        assert 'TestModelD' in model_names
        assert 'TestModelE' in model_names

    def test_discover_models_from_app_with_filterable_only(self):
        """Test discovering only filterable models from app"""
        discovered_models = self.discovery_service.discover_models_from_app(
            'filtering', base_model_class=BaseFilterableModel
        )
        
        model_names = [model.__name__ for model in discovered_models]
        
        # Should only include filterable models
        assert 'TestModelA' in model_names
        assert 'TestModelB' in model_names
        assert 'TestModelD' in model_names
        # TestModelE should not be included because it only inherits from aggregatable
        assert 'TestModelE' not in model_names

    def test_discover_models_from_app_with_aggregatable_only(self):
        """Test discovering only aggregatable models from app"""
        discovered_models = self.discovery_service.discover_models_from_app(
            'filtering', base_model_class=BaseAggregatableModel
        )
        
        model_names = [model.__name__ for model in discovered_models]
        
        # Should only include aggregatable models
        assert 'TestModelA' in model_names
        assert 'TestModelB' in model_names
        assert 'TestModelE' in model_names
        # TestModelD should not be included because it only inherits from filterable
        assert 'TestModelD' not in model_names
    
    def test_discover_all_models(self):
        """Test discovering models from all installed apps"""
        discovered_models = self.discovery_service.discover_all_models()
        
        # Should at least contain our test models
        model_names = [model.__name__ for model in discovered_models]
        assert 'TestModelA' in model_names
        assert 'TestModelB' in model_names
        
    def test_detect_field_types(self):
        """Test detecting field types from model"""
        field_types = self.discovery_service.detect_field_types(TestModelA)
        
        assert 'name' in field_types
        assert field_types['name'] == 'char'
        assert 'value' in field_types
        assert field_types['value'] == 'integer'
        assert 'active' in field_types
        assert field_types['active'] == 'boolean'
        
    def test_map_relationships(self):
        """Test mapping relationships from model"""
        relationships = self.discovery_service.map_relationships(TestModelB)
        
        assert 'model_a' in relationships
        assert relationships['model_a']['type'] == 'foreignkey'
        assert relationships['model_a']['model'] == TestModelA
        
        # Test ManyToMany relationship
        many_relationships = self.discovery_service.map_relationships(TestModelD)
        assert 'relation_many' in many_relationships
        assert many_relationships['relation_many']['type'] == 'manytomany'
        assert many_relationships['relation_many']['model'] == TestModelA
        
        # Test OneToOne relationship
        print("\nDirect field check:", TestModelE._meta.get_field('related_one').__class__.__name__)
        print("Is OneToOneField:", isinstance(TestModelE._meta.get_field('related_one'), models.OneToOneField))
        
        # Let's import the actual model discovery service class
        from ..model_discovery import ModelDiscoveryService
        discovery = ModelDiscoveryService()
        
        # Debugging imports used in the class
        import django.db.models as django_models
        print("Models module id:", id(models))
        print("Django models module id:", id(django_models))
        print("Are modules the same:", models is django_models)
        print("OneToOneField module:", models.OneToOneField.__module__)
        
        one_relationships = self.discovery_service.map_relationships(TestModelE)
        print("\nOneToOne relationships:", one_relationships)
        assert 'related_one' in one_relationships
        assert one_relationships['related_one']['type'] == 'onetoone'
        assert one_relationships['related_one']['model'] == TestModelA
        
    def test_discover_and_register(self):
        """Test discovering and registering models using the discover_and_register method"""
        # Create a new registry for this test
        from ..registry import ModelRegistry
        test_registry = ModelRegistry()
        
        # Call the discover_and_register method with the new registry
        self.discovery_service.discover_and_register(test_registry, app_labels=['filtering'])
        
        # Check if models are registered
        assert TestModelA in test_registry.registered_models
        assert TestModelB in test_registry.registered_models
        assert TestModelD in test_registry.registered_models
        assert TestModelE in test_registry.registered_models
        
        # TestModelC should not be registered
        assert TestModelC not in test_registry.registered_models
        
        # Check if field types are cached
        field_types = test_registry.get_model_field_types(TestModelA)
        assert 'name' in field_types
        assert field_types['name'] == 'char'
        
        # Check if relationships are cached
        relationships = test_registry.get_model_relationships(TestModelB)
        assert 'model_a' in relationships
        assert relationships['model_a']['type'] == 'foreignkey'
        
    def test_discover_and_register_models(self):
        """Test discover_and_register_models method"""
        # Test with specific app labels
        app_models = self.discovery_service.discover_and_register_models(app_labels=['filtering'])
        
        # Check that filtering app is in the results
        assert 'filtering' in app_models
        
        # Check that our test models were discovered
        model_names = [model.__name__ for model in app_models['filtering']]
        assert 'TestModelA' in model_names
        assert 'TestModelB' in model_names
        assert 'TestModelD' in model_names
        assert 'TestModelE' in model_names
        
        # Test with non-existent app
        app_models = self.discovery_service.discover_and_register_models(app_labels=['non_existent_app'])
        assert 'non_existent_app' not in app_models
        
        # Test without app labels (all apps)
        all_app_models = self.discovery_service.discover_and_register_models()
        assert 'filtering' in all_app_models
        
    def test_get_app_models_info(self):
        """Test get_app_models_info method"""
        models_info = self.discovery_service.get_app_models_info('filtering')
        
        # Check that our test models are in the results
        assert 'TestModelA' in models_info
        assert 'TestModelB' in models_info
        assert 'TestModelD' in models_info
        assert 'TestModelE' in models_info
        
        # Check the structure and content of model info for TestModelA
        model_a_info = models_info['TestModelA']
        assert model_a_info['model'] == TestModelA
        assert 'field_types' in model_a_info
        assert 'relationships' in model_a_info
        assert model_a_info['is_filterable'] is True
        assert model_a_info['is_aggregatable'] is True
        
        # Check field types for TestModelA
        assert 'name' in model_a_info['field_types']
        assert model_a_info['field_types']['name'] == 'char'
        
        # Check for TestModelD (only filterable)
        assert models_info['TestModelD']['is_filterable'] is True
        assert models_info['TestModelD']['is_aggregatable'] is False
        
        # Check for TestModelE (only aggregatable)
        assert models_info['TestModelE']['is_filterable'] is False
        assert models_info['TestModelE']['is_aggregatable'] is True
        
        # Check the many-to-many relationship in TestModelD
        assert 'relation_many' in models_info['TestModelD']['relationships']
        assert models_info['TestModelD']['relationships']['relation_many']['type'] == 'manytomany'


@pytest.mark.django_db
class TestAutoDiscoveryIntegration(TestCase):
    """Integration tests for auto-discovery with real models"""
    
    def test_auto_discovery_integration(self):
        """Test the complete auto-discovery workflow with model registration"""
        # Create a new registry and discovery service for this test
        from ..registry import ModelRegistry
        test_registry = ModelRegistry()
        discovery_service = ModelDiscoveryService()
        
        # Discover all models in the filtering app
        discovered_models = discovery_service.discover_models_from_app('filtering')
        
        # Register all discovered models
        for model in discovered_models:
            test_registry.register_model(model)
        
        # Get all registered model names
        registered_model_names = [model.__name__ for model in test_registry.registered_models]
        
        # Check if our test models are registered
        assert 'TestModelA' in registered_model_names
        assert 'TestModelB' in registered_model_names
        assert 'TestModelD' in registered_model_names
        assert 'TestModelE' in registered_model_names
        
        # Check field types for TestModelA
        field_types_a = test_registry.get_model_field_types(TestModelA)
        assert 'name' in field_types_a
        assert field_types_a['name'] == 'char'
        assert 'value' in field_types_a
        assert field_types_a['value'] == 'integer'
        
        # Check relationships for TestModelB
        relationships_b = test_registry.get_model_relationships(TestModelB)
        assert 'model_a' in relationships_b
        assert relationships_b['model_a']['type'] == 'foreignkey'
        
        # Create a test model instance to verify it works
        test_model = TestModelA.objects.create(name='Test', value=10)
        assert test_model.id is not None
        assert test_model.name == 'Test'
        assert test_model.value == 10 