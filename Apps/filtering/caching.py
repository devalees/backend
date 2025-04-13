from django.core.cache import cache
from django.db import models
from typing import Dict, Any, List, Optional, Union, Type
import hashlib
import json
import time

class CacheKeyGenerator:
    """
    Generates cache keys for filter and aggregation results.
    This class provides methods for generating unique and consistent cache keys
    based on model, filters, and aggregations.
    """
    
    def __init__(self):
        """Initialize the CacheKeyGenerator with a default prefix."""
        self.prefix = 'filtering'
    
    def generate_filter_key(self, model: Type[models.Model], filters: Dict[str, Any]) -> str:
        """
        Generate a cache key for filter results.
        
        Args:
            model: The model class
            filters: The filter conditions
            
        Returns:
            A unique cache key
        """
        key_parts = [
            self.prefix,
            'filter',
            model.__name__
        ]
        
        # Add each filter field and value to the key
        for field, value in sorted(filters.items()):
            key_parts.append(f"{field}={self._hash_value(value)}")
        
        return ':'.join(key_parts)
    
    def generate_aggregation_key(
        self, 
        model: Type[models.Model], 
        aggregations: Dict[str, Union[str, List[str]]], 
        group_by: Optional[List[str]] = None
    ) -> str:
        """
        Generate a cache key for aggregation results.
        
        Args:
            model: The model class
            aggregations: The aggregation conditions
            group_by: Optional list of fields to group by
            
        Returns:
            A unique cache key
        """
        key_parts = [
            self.prefix,
            'aggregation',
            model.__name__
        ]
        
        # Add each aggregation function and field to the key
        for field, agg_func in sorted(aggregations.items()):
            if isinstance(agg_func, list):
                for func in sorted(agg_func):
                    key_parts.append(f"{func}_{field}")
            else:
                key_parts.append(f"{agg_func}_{field}")
        
        if group_by:
            key_parts.append('group_by=' + '_'.join(sorted(group_by)))
        
        return ':'.join(key_parts)
    
    def generate_model_key(self, model: Type[models.Model]) -> str:
        """
        Generate a cache key for a model.
        
        Args:
            model: The model class
            
        Returns:
            A string cache key
        """
        return f"{self.prefix}:model:{model.__name__}"
    
    def generate_field_key(self, model: Type[models.Model], field: str) -> str:
        """
        Generate a cache key for a field.
        
        Args:
            model: The model class
            field: The field name
            
        Returns:
            A string cache key
        """
        return f"{self.prefix}:field:{model.__name__}:{field}"
    
    def _hash_value(self, value: Any) -> str:
        """
        Create a hash of a value for use in cache keys.
        
        Args:
            value: The value to hash
            
        Returns:
            A hash of the value
        """
        if isinstance(value, (list, tuple, set)):
            value = '_'.join(str(v) for v in sorted(value))
        elif isinstance(value, dict):
            value = '_'.join(f"{k}={v}" for k, v in sorted(value.items()))
        return hashlib.md5(str(value).encode()).hexdigest()

class CacheInvalidator:
    """Handles cache invalidation."""
    
    def __init__(self):
        """Initialize tracking dictionaries."""
        self.model_keys = {}  # model_name -> set of keys
        self.field_keys = {}  # model_name -> field_name -> set of keys
        self.all_keys = set()
    
    def _track_key(self, key, model_name, field_name=None):
        """Track a cache key."""
        self.all_keys.add(key)
        if model_name not in self.model_keys:
            self.model_keys[model_name] = set()
        self.model_keys[model_name].add(key)
        
        if field_name:
            if model_name not in self.field_keys:
                self.field_keys[model_name] = {}
            if field_name not in self.field_keys[model_name]:
                self.field_keys[model_name][field_name] = set()
            self.field_keys[model_name][field_name].add(key)
    
    def invalidate_model_cache(self, model_class):
        """Invalidate all caches for a model."""
        model_name = model_class.__name__
        if model_name in self.model_keys:
            for key in self.model_keys[model_name]:
                cache.delete(key)
            del self.model_keys[model_name]
            
            if model_name in self.field_keys:
                del self.field_keys[model_name]
    
    def invalidate_field_cache(self, model_class, field_name):
        """Invalidate caches related to a specific field."""
        model_name = model_class.__name__
        if model_name in self.field_keys and field_name in self.field_keys[model_name]:
            for key in self.field_keys[model_name][field_name]:
                cache.delete(key)
                if model_name in self.model_keys:
                    self.model_keys[model_name].discard(key)
            del self.field_keys[model_name][field_name]
    
    def invalidate_all_cache(self):
        """Invalidate all caches."""
        for key in self.all_keys:
            cache.delete(key)
        self.model_keys.clear()
        self.field_keys.clear()
        self.all_keys.clear()

class FilterCacheManager:
    """Manages caching of filter results."""
    
    def __init__(self, cache_invalidator):
        self.cache_invalidator = cache_invalidator
        self.key_generator = CacheKeyGenerator()
    
    def get_cached_filter_result(self, model_class, filters):
        """Get cached filter result."""
        key = self.key_generator.generate_filter_key(model_class, filters)
        return cache.get(key)
    
    def cache_filter_result(self, model_class, filters, result):
        """Cache filter result."""
        key = self.key_generator.generate_filter_key(model_class, filters)
        cache.set(key, result, timeout=3600)  # Cache for 1 hour
        # Track the key
        self.cache_invalidator._track_key(key, model_class.__name__)
        for field in filters.keys():
            self.cache_invalidator._track_key(key, model_class.__name__, field)
    
    def invalidate_filter_cache(self, model_class, filters):
        """Invalidate specific filter cache."""
        key = self.key_generator.generate_filter_key(model_class, filters)
        cache.delete(key)
        # Remove from tracking
        model_name = model_class.__name__
        if model_name in self.cache_invalidator.model_keys:
            self.cache_invalidator.model_keys[model_name].discard(key)
    
    def invalidate_model_filter_cache(self, model_class):
        """Invalidate all filter caches for a model."""
        self.cache_invalidator.invalidate_model_cache(model_class)

class AggregationCacheManager:
    """Manages caching of aggregation results."""
    
    def __init__(self, cache_invalidator):
        self.cache_invalidator = cache_invalidator
        self.key_generator = CacheKeyGenerator()
    
    def get_cached_aggregation_result(self, model_class, aggregations, group_by=None):
        """Get cached aggregation result."""
        key = self.key_generator.generate_aggregation_key(model_class, aggregations, group_by)
        return cache.get(key)
    
    def cache_aggregation_result(self, model_class, aggregations, group_by, result):
        """Cache aggregation result."""
        key = self.key_generator.generate_aggregation_key(model_class, aggregations, group_by)
        cache.set(key, result, timeout=3600)  # Cache for 1 hour
        # Track the key
        self.cache_invalidator._track_key(key, model_class.__name__)
        for field in aggregations.keys():
            self.cache_invalidator._track_key(key, model_class.__name__, field)
        if group_by:
            for field in group_by:
                self.cache_invalidator._track_key(key, model_class.__name__, field)
    
    def invalidate_aggregation_cache(self, model_class, aggregations, group_by=None):
        """Invalidate specific aggregation cache."""
        key = self.key_generator.generate_aggregation_key(model_class, aggregations, group_by)
        cache.delete(key)
        # Remove from tracking
        model_name = model_class.__name__
        if model_name in self.cache_invalidator.model_keys:
            self.cache_invalidator.model_keys[model_name].discard(key)
    
    def invalidate_model_aggregation_cache(self, model_class):
        """Invalidate all aggregation caches for a model."""
        self.cache_invalidator.invalidate_model_cache(model_class)