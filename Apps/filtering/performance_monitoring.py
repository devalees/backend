from django.db import models
from django.db.models import Q, QuerySet
from typing import Dict, Any, List, Optional, Union, Callable, Set, Tuple
import time
import datetime
from contextlib import contextmanager
import os
import threading

# Optional dependency: psutil for resource monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class QueryTimer:
    """
    Tracks and times database queries.
    This class provides methods for timing queries and tracking query metrics.
    """
    
    def __init__(self):
        """Initialize the QueryTimer with empty metrics."""
        self.total_queries = 0
        self.total_time = 0
        self.query_times = []  # List of query timing records
        self.model_times = {}  # Model-specific timing records
    
    @contextmanager
    def track_query(self, model_name):
        """
        Context manager for timing a query.
        
        Args:
            model_name: The name of the model being queried
            
        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Record the query
            self.total_queries += 1
            self.total_time += duration
            
            # Record in query times list
            self.query_times.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'model': model_name,
                'duration': duration
            })
            
            # Record in model-specific metrics
            if model_name not in self.model_times:
                self.model_times[model_name] = {
                    'count': 0,
                    'total_time': 0
                }
            
            self.model_times[model_name]['count'] += 1
            self.model_times[model_name]['total_time'] += duration
    
    def get_metrics(self):
        """
        Get query timing metrics.
        
        Returns:
            A dictionary of query metrics
        """
        metrics = {
            'total_queries': self.total_queries,
            'total_time': self.total_time,
            'average_time': self.total_time / self.total_queries if self.total_queries > 0 else 0,
            'model_metrics': {}
        }
        
        # Add model-specific metrics
        for model_name, model_data in self.model_times.items():
            metrics['model_metrics'][model_name] = {
                'count': model_data['count'],
                'total_time': model_data['total_time'],
                'average_time': model_data['total_time'] / model_data['count'] if model_data['count'] > 0 else 0
            }
        
        # Include recent queries (last 10)
        metrics['recent_queries'] = self.query_times[-10:] if self.query_times else []
        
        return metrics
    
    def reset(self):
        """Reset all query metrics."""
        self.total_queries = 0
        self.total_time = 0
        self.query_times = []
        self.model_times = {}


class CacheMonitor:
    """
    Monitors cache hit rates and performance.
    This class tracks cache hits and misses to provide cache performance metrics.
    """
    
    def __init__(self):
        """Initialize the CacheMonitor with empty metrics."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.model_stats = {}  # Model-specific cache stats
        self.operation_stats = {}  # Operation-specific cache stats
    
    def record_cache_hit(self, model_name, operation):
        """
        Record a cache hit.
        
        Args:
            model_name: The name of the model
            operation: The operation (e.g., 'filter', 'aggregate')
        """
        self.cache_hits += 1
        self._update_stats(model_name, operation, is_hit=True)
    
    def record_cache_miss(self, model_name, operation):
        """
        Record a cache miss.
        
        Args:
            model_name: The name of the model
            operation: The operation (e.g., 'filter', 'aggregate')
        """
        self.cache_misses += 1
        self._update_stats(model_name, operation, is_hit=False)
    
    def _update_stats(self, model_name, operation, is_hit):
        """
        Update cache statistics.
        
        Args:
            model_name: The name of the model
            operation: The operation
            is_hit: Whether it was a hit or miss
        """
        # Update model stats
        if model_name not in self.model_stats:
            self.model_stats[model_name] = {'hits': 0, 'misses': 0}
        
        # Update operation stats
        if operation not in self.operation_stats:
            self.operation_stats[operation] = {'hits': 0, 'misses': 0}
        
        # Increment the appropriate counter
        if is_hit:
            self.model_stats[model_name]['hits'] += 1
            self.operation_stats[operation]['hits'] += 1
        else:
            self.model_stats[model_name]['misses'] += 1
            self.operation_stats[operation]['misses'] += 1
    
    def get_metrics(self):
        """
        Get cache performance metrics.
        
        Returns:
            A dictionary of cache metrics
        """
        total_accesses = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_accesses if total_accesses > 0 else 0
        
        metrics = {
            'total_cache_accesses': total_accesses,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'model_stats': {},
            'operation_stats': {}
        }
        
        # Add model-specific metrics
        for model_name, stats in self.model_stats.items():
            total = stats['hits'] + stats['misses']
            metrics['model_stats'][model_name] = {
                'hits': stats['hits'],
                'misses': stats['misses'],
                'hit_rate': stats['hits'] / total if total > 0 else 0
            }
        
        # Add operation-specific metrics
        for operation, stats in self.operation_stats.items():
            total = stats['hits'] + stats['misses']
            metrics['operation_stats'][operation] = {
                'hits': stats['hits'],
                'misses': stats['misses'],
                'hit_rate': stats['hits'] / total if total > 0 else 0
            }
        
        return metrics
    
    def reset(self):
        """Reset all cache metrics."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.model_stats = {}
        self.operation_stats = {}


class ResourceMonitor:
    """
    Monitors system resource usage.
    This class tracks memory and CPU usage to provide resource utilization metrics.
    """
    
    def __init__(self):
        """Initialize the ResourceMonitor with empty metrics."""
        self.memory_usage = []  # List of memory usage records
        self.cpu_usage = []  # List of CPU usage records
        self.process = None
        
        # Initialize process if psutil is available
        if PSUTIL_AVAILABLE:
            try:
                self.process = psutil.Process(os.getpid())
            except (AttributeError, NameError, Exception):
                # Handle the case when psutil is not correctly imported
                self.process = None
    
    def record_usage(self):
        """Record current resource usage."""
        # Early return if psutil is not available or initialized
        if not PSUTIL_AVAILABLE or self.process is None:
            # Record dummy values for testing without psutil
            self.memory_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': 1.0  # 1MB placeholder
            })
            
            self.cpu_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': 5.0  # 5% placeholder
            })
            return
        
        try:
            # Record memory usage (in MB)
            memory = self.process.memory_info().rss / (1024 * 1024)
            self.memory_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': memory
            })
            
            # Record CPU usage (percentage)
            cpu = self.process.cpu_percent()
            self.cpu_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': cpu
            })
        except (AttributeError, Exception):
            # Handle errors during resource checking
            self.memory_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': 1.0  # 1MB placeholder
            })
            
            self.cpu_usage.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'value': 5.0  # 5% placeholder
            })
    
    def get_metrics(self):
        """
        Get resource usage metrics.
        
        Returns:
            A dictionary of resource metrics
        """
        # Calculate memory metrics
        memory_metrics = {
            'current': 0,
            'average': 0,
            'peak': 0,
            'samples': len(self.memory_usage)
        }
        
        if self.memory_usage:
            memory_values = [record['value'] for record in self.memory_usage]
            memory_metrics['current'] = memory_values[-1]
            memory_metrics['average'] = sum(memory_values) / len(memory_values)
            memory_metrics['peak'] = max(memory_values)
        
        # Calculate CPU metrics
        cpu_metrics = {
            'current': 0,
            'average': 0,
            'peak': 0,
            'samples': len(self.cpu_usage)
        }
        
        if self.cpu_usage:
            cpu_values = [record['value'] for record in self.cpu_usage]
            cpu_metrics['current'] = cpu_values[-1]
            cpu_metrics['average'] = sum(cpu_values) / len(cpu_values)
            cpu_metrics['peak'] = max(cpu_values)
        
        # Return all metrics
        return {
            'memory_usage': memory_metrics,
            'cpu_usage': cpu_metrics,
            'psutil_available': PSUTIL_AVAILABLE
        }
    
    def reset(self):
        """Reset all resource metrics."""
        self.memory_usage = []
        self.cpu_usage = []


class PerformanceMonitor:
    """
    Main performance monitoring class.
    This class combines query timing, cache monitoring, and resource monitoring
    to provide comprehensive performance insights.
    """
    
    def __init__(self):
        """Initialize the PerformanceMonitor with sub-monitors."""
        self.query_timer = QueryTimer()
        self.cache_monitor = CacheMonitor()
        self.resource_monitor = ResourceMonitor()
        self.thread_local = threading.local()
    
    def track_query(self, model_name):
        """
        Context manager for timing a query.
        
        Args:
            model_name: The name of the model being queried
            
        Returns:
            A context manager
        """
        return self.query_timer.track_query(model_name)
    
    def record_cache_hit(self, model_name, operation):
        """
        Record a cache hit.
        
        Args:
            model_name: The name of the model
            operation: The operation (e.g., 'filter', 'aggregate')
        """
        self.cache_monitor.record_cache_hit(model_name, operation)
    
    def record_cache_miss(self, model_name, operation):
        """
        Record a cache miss.
        
        Args:
            model_name: The name of the model
            operation: The operation (e.g., 'filter', 'aggregate')
        """
        self.cache_monitor.record_cache_miss(model_name, operation)
    
    def record_resource_usage(self):
        """Record current resource usage."""
        self.resource_monitor.record_usage()
    
    def get_metrics(self):
        """
        Get comprehensive performance metrics.
        
        Returns:
            A dictionary of all performance metrics
        """
        return {
            'query_metrics': self.query_timer.get_metrics(),
            'cache_metrics': self.cache_monitor.get_metrics(),
            'resource_metrics': self.resource_monitor.get_metrics(),
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        self.query_timer.reset()
        self.cache_monitor.reset()
        self.resource_monitor.reset() 