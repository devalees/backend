from typing import Dict, List, Set, Type, Optional
from django.db import models
from django.apps import apps
import logging

from .model_config import ModelConfig

logger = logging.getLogger(__name__)

class ModelRegistry:
    """
    Central registry for models with filtering and aggregation capabilities.
    
    This class manages the registration of models and their configurations,
    enabling the automatic application of filtering and aggregation functionality.
    """
    
    def __init__(self):
        # Maps model class to its configuration
        self._registry: Dict[Type[models.Model], ModelConfig] = {}
        # Models that have been discovered but not yet registered
        self._discovered_models: Set[Type[models.Model]] = set()
        
    def register(self, model_class: Type[models.Model]) -> ModelConfig:
        """
        Register a model for filtering and aggregation.
        
        Args:
            model_class: The Django model class to register
            
        Returns:
            The ModelConfig instance for this model
        """
        if model_class in self._registry:
            return self._registry[model_class]
        
        # Create a model configuration
        config = ModelConfig.create_for_model(model_class)
        self._registry[model_class] = config
        
        # Remove from discovered models if it was there
        self._discovered_models.discard(model_class)
        
        logger.info(f"Registered model {model_class.__name__} for filtering and aggregation")
        return config
    
    def unregister(self, model_class: Type[models.Model]) -> None:
        """
        Unregister a model from filtering and aggregation.
        
        Args:
            model_class: The Django model class to unregister
        """
        if model_class in self._registry:
            del self._registry[model_class]
            logger.info(f"Unregistered model {model_class.__name__} from filtering and aggregation")
    
    def get_config(self, model_class: Type[models.Model]) -> Optional[ModelConfig]:
        """
        Get the configuration for a registered model.
        
        Args:
            model_class: The Django model class to get configuration for
            
        Returns:
            ModelConfig for the model or None if not registered
        """
        return self._registry.get(model_class)
    
    def is_registered(self, model_class: Type[models.Model]) -> bool:
        """
        Check if a model is registered for filtering and aggregation.
        
        Args:
            model_class: The Django model class to check
            
        Returns:
            True if the model is registered, False otherwise
        """
        return model_class in self._registry
    
    def discover_models(self, app_labels: Optional[List[str]] = None) -> Set[Type[models.Model]]:
        """
        Discover all models in specified apps or all installed apps.
        
        Args:
            app_labels: Optional list of app labels to discover models from
            
        Returns:
            Set of discovered model classes
        """
        discovered = set()
        
        if app_labels:
            app_configs = [apps.get_app_config(app_label) for app_label in app_labels]
        else:
            app_configs = apps.get_app_configs()
        
        for app_config in app_configs:
            for model in app_config.get_models():
                # Skip abstract models
                if model._meta.abstract:
                    continue
                
                discovered.add(model)
                self._discovered_models.add(model)
        
        logger.info(f"Discovered {len(discovered)} models for filtering and aggregation")
        return discovered
    
    def register_discovered_models(self) -> None:
        """Register all previously discovered models."""
        models_to_register = self._discovered_models.copy()
        for model in models_to_register:
            self.register(model)
    
    @property
    def registered_models(self) -> List[Type[models.Model]]:
        """Get a list of all registered models."""
        return list(self._registry.keys())
    
    @property
    def discovered_models(self) -> List[Type[models.Model]]:
        """Get a list of all discovered but not yet registered models."""
        return list(self._discovered_models)


# Create a singleton instance of the model registry
model_registry = ModelRegistry() 