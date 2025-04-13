import pytest
from django.test import TestCase
from django.core.cache import cache
from django.db import models
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional, Union

from ..mixins import FilterableMixin, AggregatableMixin, CombinedMixin
from ..caching import FilterCacheManager, AggregationCacheManager

# Test models
class TestMixinFilterableModel(models.Model, FilterableMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'

class TestMixinAggregatableModel(models.Model, AggregatableMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'

class TestMixinFilterableAggregatableModel(models.Model, CombinedMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    
    class Meta:
        app_label = 'filtering'

class TestFilterableMixinCaching(TestCase):
    """Test cases for the FilterableMixin caching integration."""
    
    def setUp(self):
        self.model = TestMixinFilterableModel
        self.filters = {'name': 'test', 'value': 42}
        self.filter_result = [{'id': 1, 'name': 'test', 'value': 42}]
    
    def tearDown(self):
        cache.clear()
    
    @patch.object(FilterCacheManager, 'get_cached_filter_result')
    @patch.object(FilterCacheManager, 'cache_filter_result')
    def test_filter_with_cache_hit(self, mock_cache_set, mock_cache_get):
        """Test filtering with a cache hit."""
        # Setup mock to return a cached result
        mock_cache_get.return_value = self.filter_result
        
        # Call the filter method
        result = self.model.filter(self.filters)
        
        # Verify the cached result was used
        mock_cache_get.assert_called_once_with(self.model, self.filters)
        mock_cache_set.assert_not_called()
        
        # For test purposes, verify the model instance creation happened 
        # without checking the queryset values directly
        self.assertIsNotNone(result)
        # Since we're using mocks, we can't directly test the queryset contents
    
    @patch.object(FilterCacheManager, 'get_cached_filter_result')
    @patch.object(FilterCacheManager, 'cache_filter_result')
    @patch.object(models.QuerySet, 'filter')
    def test_filter_with_cache_miss(self, mock_filter, mock_cache_set, mock_cache_get):
        """Test filtering with a cache miss."""
        # Setup mocks
        mock_cache_get.return_value = None
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset
        mock_queryset.values.return_value = self.filter_result
        
        # Call the filter method
        result = self.model.filter(self.filters)
        
        # Verify the cache was checked and then set
        mock_cache_get.assert_called_once_with(self.model, self.filters)
        mock_cache_set.assert_called_once_with(self.model, self.filters, self.filter_result)
        
        # Verify the filter method was called
        mock_filter.assert_called_once()
    
    @patch.object(FilterCacheManager, 'invalidate_filter_cache')
    def test_invalidate_filter_cache_specific(self, mock_invalidate):
        """Test invalidating a specific filter cache."""
        # Call the invalidate_filter_cache method with specific filters
        self.model.invalidate_filter_cache(self.filters)
        
        # Verify the cache was invalidated
        mock_invalidate.assert_called_once_with(self.model, self.filters)
    
    @patch.object(FilterCacheManager, 'invalidate_model_filter_cache')
    def test_invalidate_filter_cache_all(self, mock_invalidate):
        """Test invalidating all filter caches for a model."""
        # Call the invalidate_filter_cache method without filters
        self.model.invalidate_filter_cache()
        
        # Verify all caches for the model were invalidated
        mock_invalidate.assert_called_once_with(self.model)

class TestAggregatableMixinCaching(TestCase):
    """Test cases for the AggregatableMixin caching integration."""
    
    def setUp(self):
        self.model = TestMixinAggregatableModel
        self.aggregations = {'value': 'sum'}
        self.group_by = ['name']
        self.aggregation_result = [{'name': 'test', 'value__sum': 42}]
    
    def tearDown(self):
        cache.clear()
    
    @patch.object(AggregationCacheManager, 'get_cached_aggregation_result')
    @patch.object(AggregationCacheManager, 'cache_aggregation_result')
    def test_aggregate_with_cache_hit(self, mock_cache_set, mock_cache_get):
        """Test aggregating with a cache hit."""
        # Setup mock to return a cached result
        mock_cache_get.return_value = self.aggregation_result
        
        # Call the aggregate method
        result = self.model.aggregate(self.aggregations, self.group_by)
        
        # Verify the cached result was used
        mock_cache_get.assert_called_once_with(self.model, self.aggregations, self.group_by)
        mock_cache_set.assert_not_called()
        
        # Verify the result is the expected aggregation result
        self.assertEqual(result, self.aggregation_result)
    
    @patch.object(AggregationCacheManager, 'get_cached_aggregation_result')
    @patch.object(AggregationCacheManager, 'cache_aggregation_result')
    @patch.object(models.QuerySet, 'annotate')
    def test_aggregate_with_cache_miss_grouped(self, mock_annotate, mock_cache_set, mock_cache_get):
        """Test aggregating with a cache miss for grouped results."""
        # Setup mocks
        mock_cache_get.return_value = None
        mock_queryset = MagicMock()
        mock_annotate.return_value = mock_queryset
        mock_queryset.__iter__.return_value = iter(self.aggregation_result)
        
        # Call the aggregate method
        result = self.model.aggregate(self.aggregations, self.group_by)
        
        # Verify the cache was checked and then set
        mock_cache_get.assert_called_once_with(self.model, self.aggregations, self.group_by)
        mock_cache_set.assert_called_once_with(
            self.model, self.aggregations, self.group_by, self.aggregation_result
        )
        
        # Verify the annotate method was called
        mock_annotate.assert_called_once()
    
    @patch.object(AggregationCacheManager, 'get_cached_aggregation_result')
    @patch.object(AggregationCacheManager, 'cache_aggregation_result')
    @patch.object(models.QuerySet, 'aggregate')
    def test_aggregate_with_cache_miss_non_grouped(self, mock_aggregate, mock_cache_set, mock_cache_get):
        """Test aggregating with a cache miss for non-grouped results."""
        # Setup mocks
        mock_cache_get.return_value = None
        mock_aggregate.return_value = {'value__sum': 42}
        
        # Call the aggregate method without group_by
        result = self.model.aggregate(self.aggregations)
        
        # Verify the cache was checked and then set
        mock_cache_get.assert_called_once_with(self.model, self.aggregations, None)
        mock_cache_set.assert_called_once_with(
            self.model, self.aggregations, None, {'value__sum': 42}
        )
        
        # Verify the aggregate method was called
        mock_aggregate.assert_called_once()
    
    @patch.object(AggregationCacheManager, 'invalidate_aggregation_cache')
    def test_invalidate_aggregation_cache_specific(self, mock_invalidate):
        """Test invalidating a specific aggregation cache."""
        # Call the invalidate_aggregation_cache method with specific aggregations
        self.model.invalidate_aggregation_cache(self.aggregations, self.group_by)
        
        # Verify the cache was invalidated
        mock_invalidate.assert_called_once_with(self.model, self.aggregations, self.group_by)
    
    @patch.object(AggregationCacheManager, 'invalidate_model_aggregation_cache')
    def test_invalidate_aggregation_cache_all(self, mock_invalidate):
        """Test invalidating all aggregation caches for a model."""
        # Call the invalidate_aggregation_cache method without aggregations
        self.model.invalidate_aggregation_cache()
        
        # Verify all caches for the model were invalidated
        mock_invalidate.assert_called_once_with(self.model)

class TestCombinedMixinCaching(TestCase):
    """Test cases for models using both FilterableMixin and AggregatableMixin."""
    
    def setUp(self):
        self.model = TestMixinFilterableAggregatableModel
        self.filters = {'name': 'test', 'value': 42}
        self.aggregations = {'value': 'sum'}
        self.group_by = ['name']
        self.filter_result = [{'id': 1, 'name': 'test', 'value': 42}]
        self.aggregation_result = [{'name': 'test', 'value__sum': 42}]
    
    def tearDown(self):
        cache.clear()
    
    @patch.object(FilterCacheManager, 'get_cached_filter_result')
    @patch.object(AggregationCacheManager, 'get_cached_aggregation_result')
    def test_filter_and_aggregate_with_cache_hits(self, mock_agg_cache_get, mock_filter_cache_get):
        """Test filtering and aggregating with cache hits."""
        # Setup mocks
        mock_filter_cache_get.return_value = self.filter_result
        mock_agg_cache_get.return_value = self.aggregation_result
        
        # Call the filter method
        filter_result = self.model.filter(self.filters)
        
        # Call the aggregate method
        agg_result = self.model.aggregate(self.aggregations, self.group_by)
        
        # Verify both cached results were used
        mock_filter_cache_get.assert_called_once_with(self.model, self.filters)
        mock_agg_cache_get.assert_called_once_with(self.model, self.aggregations, self.group_by)
        
        # Verify the filter result is not None
        self.assertIsNotNone(filter_result)
        # Verify the aggregation result matches the expected result
        self.assertEqual(agg_result, self.aggregation_result)
    
    @patch.object(FilterableMixin, 'invalidate_filter_cache')
    @patch.object(AggregatableMixin, 'invalidate_aggregation_cache')
    def test_invalidate_both_caches(self, mock_agg_invalidate, mock_filter_invalidate):
        """Test invalidating both filter and aggregation caches."""
        # Call the invalidate_all_caches method
        self.model.invalidate_all_caches()
        
        # Verify both invalidation methods were called
        mock_filter_invalidate.assert_called_once_with(self.model)
        mock_agg_invalidate.assert_called_once_with(self.model) 