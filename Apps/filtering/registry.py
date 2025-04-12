from typing import Dict, List, Type, Any, Set
from django.db import models
from django.apps import apps
from .base import BaseFilterableModel, BaseAggregatableModel

class ModelRegistry:
    """
    Registry for models that can be filtered and aggregated.
    This class manages the registration and discovery of models.
    """
    def __init__(self):
        self.registered_models: Set[Type[models.Model]] = set()
        self.model_names: Dict[str, Type[models.Model]] = {}
        self.field_types: Dict[Type[models.Model], Dict[str, str]] = {}
        self.relationships: Dict[Type[models.Model], Dict[str, Dict[str, Any]]] = {}

    def register_model(self, model: Type[models.Model]) -> None:
        """
        Register a model with the registry.
        
        Args:
            model: The model class to register
        """
        if not issubclass(model, (BaseFilterableModel, BaseAggregatableModel)):
            raise ValueError(f"Model {model.__name__} must inherit from BaseFilterableModel or BaseAggregatableModel")
        
        self.registered_models.add(model)
        self.model_names[model.__name__] = model
        
        # Cache field types and relationships
        self._cache_field_types(model)
        self._cache_relationships(model)

    def get_model_by_name(self, name: str) -> Type[models.Model]:
        """
        Get a registered model by name.
        
        Args:
            name: The name of the model to retrieve
            
        Returns:
            The model class
            
        Raises:
            KeyError: If the model is not found
        """
        if name not in self.model_names:
            raise KeyError(f"Model '{name}' not found in registry")
        return self.model_names[name]

    def get_model_field_types(self, model: Type[models.Model]) -> Dict[str, str]:
        """
        Get the field types for a model.
        
        Args:
            model: The model class
            
        Returns:
            A dictionary mapping field names to their types
        """
        if model not in self.field_types:
            self._cache_field_types(model)
        return self.field_types.get(model, {})

    def get_model_relationships(self, model: Type[models.Model]) -> Dict[str, Dict[str, Any]]:
        """
        Get the relationships for a model.
        
        Args:
            model: The model class
            
        Returns:
            A dictionary mapping field names to relationship information
        """
        if model not in self.relationships:
            self._cache_relationships(model)
        return self.relationships.get(model, {})

    def auto_discover_models(self, app_label: str) -> None:
        """
        Automatically discover and register models from a Django app.
        
        Args:
            app_label: The label of the Django app to discover models from
        """
        app_config = apps.get_app_config(app_label)
        for model in app_config.get_models():
            if issubclass(model, (BaseFilterableModel, BaseAggregatableModel)):
                self.register_model(model)

    def _cache_field_types(self, model: Type[models.Model]) -> None:
        """
        Cache the field types for a model.
        
        Args:
            model: The model class
        """
        field_types = {}
        type_mapping = {
            'CharField': 'char',
            'TextField': 'text',
            'IntegerField': 'integer',
            'DecimalField': 'decimal',
            'FloatField': 'float',
            'BooleanField': 'boolean',
            'DateTimeField': 'datetime',
            'DateField': 'date',
            'TimeField': 'time',
            'EmailField': 'email',
            'URLField': 'url',
            'UUIDField': 'uuid',
            'JSONField': 'json',
        }
        
        for field in model._meta.fields:
            field_type = field.get_internal_type()
            normalized_type = type_mapping.get(field_type, field_type.lower())
            field_types[field.name] = normalized_type
        
        self.field_types[model] = field_types

    def _cache_relationships(self, model: Type[models.Model]) -> None:
        """
        Cache the relationships for a model.
        
        Args:
            model: The model class
        """
        relationships = {}
        
        for field in model._meta.fields:
            if isinstance(field, (models.ForeignKey, models.ManyToManyField, models.OneToOneField)):
                relationships[field.name] = {
                    'type': field.get_internal_type().lower(),
                    'model': field.related_model,
                    'field': field
                }
        
        self.relationships[model] = relationships 

# Create a singleton instance of the registry
model_registry = ModelRegistry() 