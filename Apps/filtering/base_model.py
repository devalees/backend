from django.db import models
from typing import List, Dict, Any, Optional, Type, ClassVar

from .mixins import FilterableMixin, AggregatableMixin
from .model_registry import model_registry


class FilterableModel(models.Model, FilterableMixin):
    """
    Base model class that provides filtering capabilities.
    
    All models inheriting from this class will automatically have
    filtering functionality applied to them.
    
    Example:
        ```python
        from Apps.filtering.base_model import FilterableModel
        
        class YourModel(FilterableModel):
            name = models.CharField(max_length=100)
            
            class FilterConfig:
                text = ['name']
        ```
    """
    
    class Meta:
        abstract = True
    
    def __init_subclass__(cls, **kwargs):
        """Register subclasses with the model registry when they are defined."""
        super().__init_subclass__(**kwargs)
        
        # Only register non-abstract models
        if not getattr(cls._meta, 'abstract', False):
            model_registry.register(cls)


class AggregatableModel(models.Model, AggregatableMixin):
    """
    Base model class that provides aggregation capabilities.
    
    All models inheriting from this class will automatically have
    aggregation functionality applied to them.
    
    Example:
        ```python
        from Apps.filtering.base_model import AggregatableModel
        
        class YourModel(AggregatableModel):
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class AggregationConfig:
                sum = ['amount']
        ```
    """
    
    class Meta:
        abstract = True
    
    def __init_subclass__(cls, **kwargs):
        """Register subclasses with the model registry when they are defined."""
        super().__init_subclass__(**kwargs)
        
        # Only register non-abstract models
        if not getattr(cls._meta, 'abstract', False):
            model_registry.register(cls)


class FilterableAggregatableModel(FilterableModel, AggregatableModel):
    """
    Base model class that provides both filtering and aggregation capabilities.
    
    All models inheriting from this class will automatically have both
    filtering and aggregation functionality applied to them.
    
    Example:
        ```python
        from Apps.filtering.base_model import FilterableAggregatableModel
        
        class YourModel(FilterableAggregatableModel):
            name = models.CharField(max_length=100)
            amount = models.DecimalField(max_digits=10, decimal_places=2)
            
            class FilterConfig:
                text = ['name']
                
            class AggregationConfig:
                sum = ['amount']
        ```
    """
    
    class Meta:
        abstract = True 