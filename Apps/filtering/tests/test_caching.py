import pytest
from django.test import TestCase
from django.core.cache import cache
from django.db import models
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional, Union

from ..caching import (
    FilterCacheManager,
    AggregationCacheManager,
    CacheKeyGenerator,
    CacheInvalidator
)

# Test models
class CacheTestModel(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'
        managed = False

class CacheTestFilterableModel(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'
        managed = False
    
    @classmethod
    def filter(cls, filters):
        # Mock implementation for testing
        return cls.objects.filter(**filters)
    
    @classmethod
    def aggregate(cls, aggregations, group_by=None):
        # Mock implementation for testing
        return cls.objects.aggregate(**aggregations)

class TestCacheKeyGenerator(TestCase):
    """Test cases for the CacheKeyGenerator class."""
    
    def setUp(self):
        self.key_generator = CacheKeyGenerator()
        self.model = CacheTestModel
        self.filters = {'name': 'test', 'value': 42}
        self.aggregations = {'value': 'sum'}
        self.group_by = ['name']
    
    def test_generate_filter_key(self):
        """Test generating a cache key for filter results."""
        key = self.key_generator.generate_filter_key(self.model, self.filters)
        self.assertIsInstance(key, str)
        self.assertIn(self.model.__name__, key)
        self.assertIn('name', key)
        self.assertIn('value', key)
    
    def test_generate_aggregation_key(self):
        """Test generating a cache key for aggregation results."""
        key = self.key_generator.generate_aggregation_key(
            self.model, self.aggregations, self.group_by
        )
        self.assertIsInstance(key, str)
        self.assertIn(self.model.__name__, key)
        self.assertIn('value', key)
        self.assertIn('sum', key)
        self.assertIn('name', key)
    
    def test_generate_model_key(self):
        """Test generating a cache key for a model."""
        key = self.key_generator.generate_model_key(self.model)
        self.assertIsInstance(key, str)
        self.assertIn(self.model.__name__, key)
    
    def test_generate_field_key(self):
        """Test generating a cache key for a field."""
        key = self.key_generator.generate_field_key(self.model, 'name')
        self.assertIsInstance(key, str)
        self.assertIn(self.model.__name__, key)
        self.assertIn('name', key)

class TestFilterCacheManager(TestCase):
    """Test cases for the FilterCacheManager class."""
    
    def setUp(self):
        self.cache_invalidator = CacheInvalidator()
        self.manager = FilterCacheManager(self.cache_invalidator)
        self.model = CacheTestModel
        self.filters = {'name': 'test'}
        self.result = [{'id': 1, 'name': 'test'}]
    
    def tearDown(self):
        cache.clear()
    
    def test_cache_filter_result(self):
        """Test caching a filter result."""
        self.manager.cache_filter_result(self.model, self.filters, self.result)
        key = self.manager.key_generator.generate_filter_key(self.model, self.filters)
        
        # Check that the result was cached
        self.assertEqual(cache.get(key), self.result)
        
        # Check that the key was tracked
        self.assertIn(key, self.cache_invalidator.model_keys[self.model.__name__])
        self.assertIn(key, self.cache_invalidator.field_keys[self.model.__name__]['name'])
    
    def test_invalidate_model_filter_cache(self):
        """Test invalidating all filter caches for a model."""
        # Cache a result first
        self.manager.cache_filter_result(self.model, self.filters, self.result)
        key = self.manager.key_generator.generate_filter_key(self.model, self.filters)
        
        # Verify it's cached
        self.assertIsNotNone(cache.get(key))
        
        # Invalidate the cache
        self.manager.invalidate_model_filter_cache(self.model)
        
        # Verify it's no longer cached
        self.assertIsNone(cache.get(key))
        
        # Verify tracking is cleared
        self.assertNotIn(key, self.cache_invalidator.model_keys.get(self.model.__name__, set()))

class TestAggregationCacheManager(TestCase):
    """Test cases for the AggregationCacheManager class."""
    
    def setUp(self):
        self.cache_invalidator = CacheInvalidator()
        self.manager = AggregationCacheManager(self.cache_invalidator)
        self.model = CacheTestModel
        self.aggregations = {'value': 'count'}
        self.group_by = ['name']
        self.result = {'count': 42}
    
    def tearDown(self):
        cache.clear()
    
    def test_cache_aggregation_result(self):
        """Test caching an aggregation result."""
        self.manager.cache_aggregation_result(
            self.model, 
            self.aggregations, 
            self.group_by, 
            self.result
        )
        key = self.manager.key_generator.generate_aggregation_key(
            self.model, 
            self.aggregations, 
            self.group_by
        )
        
        # Check that the result was cached
        self.assertEqual(cache.get(key), self.result)
        
        # Check that the key was tracked
        self.assertIn(key, self.cache_invalidator.model_keys[self.model.__name__])
        self.assertIn(key, self.cache_invalidator.field_keys[self.model.__name__]['value'])
        self.assertIn(key, self.cache_invalidator.field_keys[self.model.__name__]['name'])
    
    def test_invalidate_model_aggregation_cache(self):
        """Test invalidating all aggregation caches for a model."""
        # Cache a result first
        self.manager.cache_aggregation_result(
            self.model,
            self.aggregations,
            self.group_by,
            self.result
        )
        key = self.manager.key_generator.generate_aggregation_key(
            self.model,
            self.aggregations,
            self.group_by
        )
        
        # Verify it's cached
        self.assertIsNotNone(cache.get(key))
        
        # Invalidate the cache
        self.manager.invalidate_model_aggregation_cache(self.model)
        
        # Verify it's no longer cached
        self.assertIsNone(cache.get(key))
        
        # Verify tracking is cleared
        self.assertNotIn(key, self.cache_invalidator.model_keys.get(self.model.__name__, set()))

class TestCacheInvalidator(TestCase):
    """Test cases for the CacheInvalidator class."""
    
    def setUp(self):
        self.invalidator = CacheInvalidator()
        self.filter_manager = FilterCacheManager(self.invalidator)
        self.aggregation_manager = AggregationCacheManager(self.invalidator)
        self.model = CacheTestModel
        
        # Set up some test data
        self.filter_data = {'name': 'test'}
        self.filter_result = [{'id': 1, 'name': 'test'}]
        self.aggregation_data = {'value': 'count'}
        self.group_by = ['name']
        self.aggregation_result = {'count': 42}
        
        # Cache some test results
        self.filter_manager.cache_filter_result(
            self.model, 
            self.filter_data, 
            self.filter_result
        )
        self.aggregation_manager.cache_aggregation_result(
            self.model,
            self.aggregation_data,
            self.group_by,
            self.aggregation_result
        )
        
        # Store the keys for verification
        self.filter_key = self.filter_manager.key_generator.generate_filter_key(
            self.model, 
            self.filter_data
        )
        self.aggregation_key = self.aggregation_manager.key_generator.generate_aggregation_key(
            self.model,
            self.aggregation_data,
            self.group_by
        )
    
    def tearDown(self):
        cache.clear()
    
    def test_invalidate_model_cache(self):
        """Test invalidating all caches for a model."""
        # Verify data is cached
        self.assertIsNotNone(cache.get(self.filter_key))
        self.assertIsNotNone(cache.get(self.aggregation_key))
        
        # Invalidate model cache
        self.invalidator.invalidate_model_cache(self.model)
        
        # Verify data is no longer cached
        self.assertIsNone(cache.get(self.filter_key))
        self.assertIsNone(cache.get(self.aggregation_key))
        
        # Verify tracking is cleared
        self.assertNotIn(self.model.__name__, self.invalidator.model_keys)
    
    def test_invalidate_field_cache(self):
        """Test invalidating caches for a specific field."""
        # Verify data is cached
        self.assertIsNotNone(cache.get(self.filter_key))
        self.assertIsNotNone(cache.get(self.aggregation_key))
        
        # Invalidate field cache
        self.invalidator.invalidate_field_cache(self.model, 'name')
        
        # Verify data is no longer cached
        self.assertIsNone(cache.get(self.filter_key))
        self.assertIsNone(cache.get(self.aggregation_key))
        
        # Verify tracking is cleared
        self.assertNotIn('name', self.invalidator.field_keys.get(self.model.__name__, {}))
    
    def test_invalidate_all_cache(self):
        """Test invalidating all caches."""
        # Verify data is cached
        self.assertIsNotNone(cache.get(self.filter_key))
        self.assertIsNotNone(cache.get(self.aggregation_key))
        
        # Invalidate all caches
        self.invalidator.invalidate_all_cache()
        
        # Verify data is no longer cached
        self.assertIsNone(cache.get(self.filter_key))
        self.assertIsNone(cache.get(self.aggregation_key))
        
        # Verify all tracking is cleared
        self.assertEqual(len(self.invalidator.model_keys), 0)
        self.assertEqual(len(self.invalidator.field_keys), 0)

class TestCachingIntegration(TestCase):
    """Integration tests for the caching system."""
    
    def setUp(self):
        self.cache_invalidator = CacheInvalidator()
        self.filter_manager = FilterCacheManager(self.cache_invalidator)
        self.aggregation_manager = AggregationCacheManager(self.cache_invalidator)
        self.model = CacheTestModel
        self.filters = {'name': 'test', 'value': 42}
        self.aggregations = {'value': 'sum'}
        self.group_by = ['name']
        self.filter_result = [{'id': 1, 'name': 'test', 'value': 42}]
        self.aggregation_result = {'value__sum': 42}
    
    def tearDown(self):
        cache.clear()
    
    def test_cache_invalidation_workflow(self):
        """Test the complete workflow for cache invalidation."""
        # Cache filter and aggregation results
        self.filter_manager.cache_filter_result(
            self.model, self.filters, self.filter_result
        )
        self.aggregation_manager.cache_aggregation_result(
            self.model, self.aggregations, self.group_by, self.aggregation_result
        )
        
        # Get the cache keys
        filter_key = self.filter_manager.key_generator.generate_filter_key(
            self.model, self.filters
        )
        aggregation_key = self.aggregation_manager.key_generator.generate_aggregation_key(
            self.model, self.aggregations, self.group_by
        )
        
        # Verify results are cached
        self.assertEqual(cache.get(filter_key), self.filter_result)
        self.assertEqual(cache.get(aggregation_key), self.aggregation_result)
        
        # Invalidate all caches for the model
        self.cache_invalidator.invalidate_model_cache(self.model)
        
        # Verify caches are invalidated
        self.assertIsNone(cache.get(filter_key))
        self.assertIsNone(cache.get(aggregation_key))
        
        # Verify tracking is cleared
        self.assertNotIn(self.model.__name__, self.cache_invalidator.model_keys) 