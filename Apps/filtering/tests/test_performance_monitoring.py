import os
import pytest
import time
from unittest import mock
from django.test import TestCase, override_settings
from django.db import models
from django.core.cache import cache

from ..models import (
    TestFilterableModel,
    TestAggregatableModel,
    TestCombinedModel
)

from ..performance_monitoring import (
    PerformanceMonitor,
    QueryTimer,
    CacheMonitor,
    ResourceMonitor,
    PSUTIL_AVAILABLE
)

# Point to test settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'Apps.filtering.tests.test_settings'

# Create a mock for psutil if it's not available
if not PSUTIL_AVAILABLE:
    psutil_mock = mock.MagicMock()
    psutil_mock.Process.return_value.memory_info.return_value.rss = 1024 * 1024  # 1MB
    psutil_mock.Process.return_value.cpu_percent.return_value = 5.0
    modules = {
        'psutil': psutil_mock
    }
    patcher = mock.patch.dict('sys.modules', modules)
    patcher.start()

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestPerformanceMonitor(TestCase):
    """Test cases for the main PerformanceMonitor class."""
    
    def setUp(self):
        # Register the models
        TestFilterableModel.register_model_class()
        TestAggregatableModel.register_model_class()
        TestCombinedModel.register_model_class()
        
        # Create test data
        self.model1 = TestFilterableModel.objects.create(
            name="Test 1", 
            description="Description 1", 
            age=25, 
            is_active=True
        )
        self.model2 = TestFilterableModel.objects.create(
            name="Test 2", 
            description="Description 2", 
            age=30, 
            is_active=False
        )
        
        # Create performance monitor instance
        self.monitor = PerformanceMonitor()
        
    def tearDown(self):
        cache.clear()
        # Reset performance metrics
        self.monitor.reset_metrics()
    
    def test_performance_monitor_initialization(self):
        """Test that the performance monitor initializes correctly."""
        self.assertIsInstance(self.monitor, PerformanceMonitor)
        self.assertIsInstance(self.monitor.query_timer, QueryTimer)
        self.assertIsInstance(self.monitor.cache_monitor, CacheMonitor)
        self.assertIsInstance(self.monitor.resource_monitor, ResourceMonitor)
    
    def test_performance_monitor_get_metrics(self):
        """Test getting comprehensive metrics."""
        metrics = self.monitor.get_metrics()
        
        # Check the metrics structure
        self.assertIn('query_metrics', metrics)
        self.assertIn('cache_metrics', metrics)
        self.assertIn('resource_metrics', metrics)
    
    def test_performance_monitor_reset_metrics(self):
        """Test resetting all metrics."""
        # Record a few metrics
        with self.monitor.track_query('test_model'):
            time.sleep(0.01)  # Small delay to register time
        
        self.monitor.record_cache_hit('test_model', 'filter')
        self.monitor.record_resource_usage()
        
        # Get metrics before reset
        before_reset = self.monitor.get_metrics()
        
        # Reset metrics
        self.monitor.reset_metrics()
        
        # Get metrics after reset
        after_reset = self.monitor.get_metrics()
        
        # Check query metrics
        self.assertTrue(before_reset['query_metrics']['total_queries'] > 0)
        self.assertEqual(after_reset['query_metrics']['total_queries'], 0)
        
        # Check cache metrics
        self.assertTrue(before_reset['cache_metrics']['total_cache_accesses'] > 0)
        self.assertEqual(after_reset['cache_metrics']['total_cache_accesses'], 0)

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestQueryTimer(TestCase):
    """Test cases for the QueryTimer class."""
    
    def setUp(self):
        self.query_timer = QueryTimer()
    
    def tearDown(self):
        self.query_timer.reset()
    
    def test_query_timer_initialization(self):
        """Test that the query timer initializes correctly."""
        self.assertEqual(self.query_timer.total_queries, 0)
        self.assertEqual(self.query_timer.total_time, 0)
        self.assertEqual(len(self.query_timer.query_times), 0)
        self.assertEqual(len(self.query_timer.model_times), 0)
    
    def test_track_query_context_manager(self):
        """Test tracking query time using context manager."""
        with self.query_timer.track_query('test_model'):
            time.sleep(0.01)  # Small delay to register time
        
        # Verify query was tracked
        self.assertEqual(self.query_timer.total_queries, 1)
        self.assertTrue(self.query_timer.total_time > 0)
        self.assertTrue('test_model' in self.query_timer.model_times)
        self.assertEqual(len(self.query_timer.query_times), 1)
    
    def test_multiple_queries(self):
        """Test tracking multiple queries."""
        models = ['model1', 'model2', 'model3']
        
        for model in models:
            with self.query_timer.track_query(model):
                time.sleep(0.01)  # Small delay
        
        # Verify all queries were tracked
        self.assertEqual(self.query_timer.total_queries, 3)
        self.assertTrue(self.query_timer.total_time > 0)
        
        # Check model-specific metrics
        for model in models:
            self.assertTrue(model in self.query_timer.model_times)
            self.assertTrue(self.query_timer.model_times[model]['total_time'] > 0)
            self.assertEqual(self.query_timer.model_times[model]['count'], 1)
    
    def test_get_metrics(self):
        """Test getting query metrics."""
        # Record some metrics
        with self.query_timer.track_query('test_model'):
            time.sleep(0.01)
        
        metrics = self.query_timer.get_metrics()
        
        # Check metrics
        self.assertEqual(metrics['total_queries'], 1)
        self.assertTrue(metrics['total_time'] > 0)
        self.assertTrue('test_model' in metrics['model_metrics'])
        self.assertEqual(metrics['model_metrics']['test_model']['count'], 1)
        self.assertTrue(metrics['model_metrics']['test_model']['total_time'] > 0)
        self.assertTrue(metrics['model_metrics']['test_model']['average_time'] > 0)
    
    def test_query_timer_reset(self):
        """Test resetting query metrics."""
        # Record some metrics
        with self.query_timer.track_query('test_model'):
            time.sleep(0.01)
        
        # Verify metrics exist
        self.assertEqual(self.query_timer.total_queries, 1)
        
        # Reset metrics
        self.query_timer.reset()
        
        # Verify metrics were reset
        self.assertEqual(self.query_timer.total_queries, 0)
        self.assertEqual(self.query_timer.total_time, 0)
        self.assertEqual(len(self.query_timer.query_times), 0)
        self.assertEqual(len(self.query_timer.model_times), 0)

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestCacheMonitor(TestCase):
    """Test cases for the CacheMonitor class."""
    
    def setUp(self):
        self.cache_monitor = CacheMonitor()
    
    def tearDown(self):
        self.cache_monitor.reset()
    
    def test_cache_monitor_initialization(self):
        """Test that the cache monitor initializes correctly."""
        self.assertEqual(self.cache_monitor.cache_hits, 0)
        self.assertEqual(self.cache_monitor.cache_misses, 0)
        self.assertEqual(len(self.cache_monitor.model_stats), 0)
        self.assertEqual(len(self.cache_monitor.operation_stats), 0)
    
    def test_record_cache_hit(self):
        """Test recording a cache hit."""
        self.cache_monitor.record_cache_hit('test_model', 'filter')
        
        # Verify hit was recorded
        self.assertEqual(self.cache_monitor.cache_hits, 1)
        self.assertEqual(self.cache_monitor.cache_misses, 0)
        self.assertEqual(self.cache_monitor.model_stats['test_model']['hits'], 1)
        self.assertEqual(self.cache_monitor.operation_stats['filter']['hits'], 1)
    
    def test_record_cache_miss(self):
        """Test recording a cache miss."""
        self.cache_monitor.record_cache_miss('test_model', 'filter')
        
        # Verify miss was recorded
        self.assertEqual(self.cache_monitor.cache_hits, 0)
        self.assertEqual(self.cache_monitor.cache_misses, 1)
        self.assertEqual(self.cache_monitor.model_stats['test_model']['misses'], 1)
        self.assertEqual(self.cache_monitor.operation_stats['filter']['misses'], 1)
    
    def test_multiple_cache_operations(self):
        """Test recording multiple cache operations."""
        operations = [
            ('model1', 'filter', True),
            ('model1', 'aggregate', False),
            ('model2', 'filter', True),
            ('model2', 'filter', True),
        ]
        
        for model, operation, is_hit in operations:
            if is_hit:
                self.cache_monitor.record_cache_hit(model, operation)
            else:
                self.cache_monitor.record_cache_miss(model, operation)
        
        # Verify all operations were recorded
        self.assertEqual(self.cache_monitor.cache_hits, 3)
        self.assertEqual(self.cache_monitor.cache_misses, 1)
        
        # Check model-specific metrics
        self.assertEqual(self.cache_monitor.model_stats['model1']['hits'], 1)
        self.assertEqual(self.cache_monitor.model_stats['model1']['misses'], 1)
        self.assertEqual(self.cache_monitor.model_stats['model2']['hits'], 2)
        self.assertEqual(self.cache_monitor.model_stats['model2']['misses'], 0)
        
        # Check operation-specific metrics
        self.assertEqual(self.cache_monitor.operation_stats['filter']['hits'], 3)
        self.assertEqual(self.cache_monitor.operation_stats['filter']['misses'], 0)
        self.assertEqual(self.cache_monitor.operation_stats['aggregate']['hits'], 0)
        self.assertEqual(self.cache_monitor.operation_stats['aggregate']['misses'], 1)
    
    def test_get_metrics(self):
        """Test getting cache metrics."""
        # Record some metrics
        self.cache_monitor.record_cache_hit('test_model', 'filter')
        self.cache_monitor.record_cache_miss('test_model', 'aggregate')
        
        metrics = self.cache_monitor.get_metrics()
        
        # Check metrics
        self.assertEqual(metrics['total_cache_accesses'], 2)
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_misses'], 1)
        self.assertEqual(metrics['hit_rate'], 0.5)
        
        # Check model-specific metrics
        self.assertEqual(metrics['model_stats']['test_model']['hits'], 1)
        self.assertEqual(metrics['model_stats']['test_model']['misses'], 1)
        self.assertEqual(metrics['model_stats']['test_model']['hit_rate'], 0.5)
        
        # Check operation-specific metrics
        self.assertEqual(metrics['operation_stats']['filter']['hits'], 1)
        self.assertEqual(metrics['operation_stats']['filter']['misses'], 0)
        self.assertEqual(metrics['operation_stats']['filter']['hit_rate'], 1.0)
        self.assertEqual(metrics['operation_stats']['aggregate']['hits'], 0)
        self.assertEqual(metrics['operation_stats']['aggregate']['misses'], 1)
        self.assertEqual(metrics['operation_stats']['aggregate']['hit_rate'], 0.0)
    
    def test_cache_monitor_reset(self):
        """Test resetting cache metrics."""
        # Record some metrics
        self.cache_monitor.record_cache_hit('test_model', 'filter')
        self.cache_monitor.record_cache_miss('test_model', 'aggregate')
        
        # Verify metrics exist
        self.assertEqual(self.cache_monitor.cache_hits, 1)
        self.assertEqual(self.cache_monitor.cache_misses, 1)
        
        # Reset metrics
        self.cache_monitor.reset()
        
        # Verify metrics were reset
        self.assertEqual(self.cache_monitor.cache_hits, 0)
        self.assertEqual(self.cache_monitor.cache_misses, 0)
        self.assertEqual(len(self.cache_monitor.model_stats), 0)
        self.assertEqual(len(self.cache_monitor.operation_stats), 0)

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestResourceMonitor(TestCase):
    """Test cases for the ResourceMonitor class."""
    
    def setUp(self):
        self.resource_monitor = ResourceMonitor()
    
    def tearDown(self):
        self.resource_monitor.reset()
    
    def test_resource_monitor_initialization(self):
        """Test that the resource monitor initializes correctly."""
        self.assertEqual(len(self.resource_monitor.memory_usage), 0)
        self.assertEqual(len(self.resource_monitor.cpu_usage), 0)
    
    def test_record_resource_usage(self):
        """Test recording resource usage."""
        # Record resource usage directly (no mock needed with fallback)
        self.resource_monitor.record_usage()
        
        # Verify usage was recorded
        self.assertEqual(len(self.resource_monitor.memory_usage), 1)
        self.assertEqual(len(self.resource_monitor.cpu_usage), 1)
        
        # Values should be recorded even without psutil
        self.assertTrue(self.resource_monitor.memory_usage[0]['value'] > 0)
        self.assertTrue(self.resource_monitor.cpu_usage[0]['value'] > 0)
    
    def test_multiple_resource_recordings(self):
        """Test recording multiple resource usage samples."""
        # Record multiple times
        for _ in range(3):
            self.resource_monitor.record_usage()
            
        # Verify recording count
        self.assertEqual(len(self.resource_monitor.memory_usage), 3)
        self.assertEqual(len(self.resource_monitor.cpu_usage), 3)
    
    def test_get_metrics(self):
        """Test getting resource metrics."""
        # Record resource usage a few times
        for _ in range(3):
            self.resource_monitor.record_usage()
        
        metrics = self.resource_monitor.get_metrics()
        
        # Check metrics structure
        self.assertIn('memory_usage', metrics)
        self.assertIn('cpu_usage', metrics)
        self.assertIn('current', metrics['memory_usage'])
        self.assertIn('average', metrics['memory_usage'])
        self.assertIn('peak', metrics['memory_usage'])
        
        # Check that values exist
        self.assertTrue(metrics['memory_usage']['current'] > 0)
        self.assertTrue(metrics['memory_usage']['peak'] > 0)
        self.assertTrue(metrics['cpu_usage']['current'] > 0)
        self.assertTrue(metrics['cpu_usage']['peak'] > 0)
    
    def test_resource_monitor_reset(self):
        """Test resetting resource metrics."""
        # Record some resource usage
        self.resource_monitor.record_usage()
        
        # Verify metrics exist
        self.assertEqual(len(self.resource_monitor.memory_usage), 1)
        self.assertEqual(len(self.resource_monitor.cpu_usage), 1)
        
        # Reset metrics
        self.resource_monitor.reset()
        
        # Verify metrics were reset
        self.assertEqual(len(self.resource_monitor.memory_usage), 0)
        self.assertEqual(len(self.resource_monitor.cpu_usage), 0)

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestFilterableMixinWithPerformanceMonitoring(TestCase):
    """Test integration of performance monitoring with FilterableMixin."""
    
    def setUp(self):
        # Register the models
        TestFilterableModel.register_model_class()
        
        # Create test data
        self.model1 = TestFilterableModel.objects.create(
            name="Test 1", 
            description="Description 1", 
            age=25, 
            is_active=True
        )
        self.model2 = TestFilterableModel.objects.create(
            name="Test 2", 
            description="Description 2", 
            age=30, 
            is_active=False
        )
        
        # Clear the cache
        cache.clear()
        
        # Initialize the performance monitor
        self.monitor = PerformanceMonitor()
        
        # Replace the model's performance monitor with our test instance
        self._original_monitor = getattr(TestFilterableModel, '_performance_monitor', None)
        TestFilterableModel._performance_monitor = self.monitor
    
    def tearDown(self):
        # Restore the original performance monitor
        if self._original_monitor is not None:
            TestFilterableModel._performance_monitor = self._original_monitor
        else:
            delattr(TestFilterableModel, '_performance_monitor')
        
        # Clear the cache
        cache.clear()
    
    def test_filter_performance_monitoring(self):
        """Test that filter operations are monitored."""
        # Initial metrics
        before_metrics = self.monitor.get_metrics()
        
        # Perform a filter operation with cache miss
        TestFilterableModel.filter({'name': 'Test'})
        
        # Metrics after first filter (cache miss)
        after_first_filter_metrics = self.monitor.get_metrics()
        
        # Perform the same filter operation again (cache hit)
        TestFilterableModel.filter({'name': 'Test'})
        
        # Metrics after second filter (cache hit)
        after_second_filter_metrics = self.monitor.get_metrics()
        
        # Check query metrics
        self.assertEqual(before_metrics['query_metrics']['total_queries'], 0)
        self.assertTrue(after_first_filter_metrics['query_metrics']['total_queries'] > 0)
        
        # Check cache metrics
        self.assertEqual(before_metrics['cache_metrics']['total_cache_accesses'], 0)
        self.assertEqual(after_first_filter_metrics['cache_metrics']['cache_misses'], 1)
        self.assertEqual(after_second_filter_metrics['cache_metrics']['cache_hits'], 1)
    
    def test_performance_monitoring_with_different_filters(self):
        """Test monitoring with different filter operations."""
        # Perform different filter operations
        filters = [
            {'name': 'Test 1'},
            {'age': 25},
            {'is_active': True},
            {'name': 'Test', 'is_active': True}
        ]
        
        # Execute each filter twice to test both cache miss and hit
        for filter_dict in filters:
            # First execution (cache miss)
            TestFilterableModel.filter(filter_dict)
            
            # Second execution (cache hit)
            TestFilterableModel.filter(filter_dict)
        
        # Get final metrics
        metrics = self.monitor.get_metrics()
        
        # Check cache metrics
        self.assertEqual(metrics['cache_metrics']['cache_hits'], 4)  # One hit for each filter
        self.assertEqual(metrics['cache_metrics']['cache_misses'], 4)  # One miss for each filter
        self.assertEqual(metrics['cache_metrics']['hit_rate'], 0.5)  # 50% hit rate
        
        # Check query metrics - should have recorded one query per cache miss
        self.assertEqual(metrics['query_metrics']['total_queries'], 4) 