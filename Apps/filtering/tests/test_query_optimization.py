import os
import pytest
from django.db import models
from django.test import TestCase, override_settings
from django.db.models import Q, QuerySet
from django.db.models.sql import Query
from django.db.models.sql import Query as SQLQuery
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import WhereNode
from typing import Dict, Any, List, Optional, Union, Callable

from ..query_optimization import (
    QueryOptimizer,
    QueryPlanGenerator,
    IndexOptimizer,
    JoinOptimizer
)
from ..models import (
    TestFilterableModel,
    TestAggregatableModel,
    TestCombinedModel
)

# Point to our test settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'Apps.filtering.tests.test_settings'

@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class TestQueryOptimizer(TestCase):
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
        self.model3 = TestFilterableModel.objects.create(
            name="Another", 
            description="Description 3", 
            age=35, 
            is_active=True
        )
    
    def test_query_optimizer_initialization(self):
        """Test that QueryOptimizer initializes correctly"""
        optimizer = QueryOptimizer()
        self.assertIsNotNone(optimizer)
        self.assertIsInstance(optimizer, QueryOptimizer)
        self.assertIsInstance(optimizer.plan_generator, QueryPlanGenerator)
        self.assertIsInstance(optimizer.index_optimizer, IndexOptimizer)
        self.assertIsInstance(optimizer.join_optimizer, JoinOptimizer)
    
    def test_optimize_query(self):
        """Test that optimize_query returns an optimized queryset"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the original queryset
        original_queryset = TestFilterableModel.filter(filters)
        
        # Optimize the queryset
        optimizer = QueryOptimizer()
        optimized_queryset = optimizer.optimize_query(original_queryset)
        
        # Check that the optimized queryset returns the same results
        self.assertEqual(original_queryset.count(), optimized_queryset.count())
        self.assertEqual(list(original_queryset), list(optimized_queryset))
    
    def test_optimize_query_with_complex_filters(self):
        """Test that optimize_query works with complex filters"""
        # Create a complex filter
        filters = {
            'name': {'startswith': 'Test', 'contains': '1'},
            'age': {'gt': 20, 'lt': 30},
            'is_active': True
        }
        
        # Get the original queryset
        original_queryset = TestFilterableModel.filter(filters)
        
        # Optimize the queryset
        optimizer = QueryOptimizer()
        optimized_queryset = optimizer.optimize_query(original_queryset)
        
        # Check that the optimized queryset returns the same results
        self.assertEqual(original_queryset.count(), optimized_queryset.count())
        self.assertEqual(list(original_queryset), list(optimized_queryset))

class TestQueryPlanGenerator(TestCase):
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
        self.model3 = TestFilterableModel.objects.create(
            name="Another", 
            description="Description 3", 
            age=35, 
            is_active=True
        )
    
    def test_query_plan_generator_initialization(self):
        """Test that QueryPlanGenerator initializes correctly"""
        generator = QueryPlanGenerator()
        self.assertIsNotNone(generator)
        self.assertIsInstance(generator, QueryPlanGenerator)
    
    def test_generate_query_plan(self):
        """Test that generate_query_plan returns a valid query plan"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Generate the query plan
        generator = QueryPlanGenerator()
        query_plan = generator.generate_query_plan(queryset)
        
        # Check that the query plan is valid
        self.assertIsNotNone(query_plan)
        self.assertIsInstance(query_plan, dict)
        self.assertIn('model', query_plan)
        self.assertIn('filters', query_plan)
        self.assertIn('joins', query_plan)
        self.assertIn('indexes', query_plan)
    
    def test_generate_query_plan_with_complex_filters(self):
        """Test that generate_query_plan works with complex filters"""
        # Create a complex filter
        filters = {
            'name': {'startswith': 'Test', 'contains': '1'},
            'age': {'gt': 20, 'lt': 30},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Generate the query plan
        generator = QueryPlanGenerator()
        query_plan = generator.generate_query_plan(queryset)
        
        # Check that the query plan is valid
        self.assertIsNotNone(query_plan)
        self.assertIsInstance(query_plan, dict)
        self.assertIn('model', query_plan)
        self.assertIn('filters', query_plan)
        self.assertIn('joins', query_plan)
        self.assertIn('indexes', query_plan)
        
        # Check that the model is correctly identified
        self.assertEqual(query_plan['model'], 'TestFilterableModel')
    
    def test_extract_filters(self):
        """Test that _extract_filters correctly extracts filters from a query"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Get the query
        query = queryset.query
        
        # Extract the filters
        generator = QueryPlanGenerator()
        extracted_filters = generator._extract_filters(query)
        
        # Check that the filters were extracted
        self.assertIsNotNone(extracted_filters)
        self.assertIsInstance(extracted_filters, dict)
    
    def test_extract_joins(self):
        """Test that _extract_joins correctly extracts joins from a query"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Get the query
        query = queryset.query
        
        # Extract the joins
        generator = QueryPlanGenerator()
        extracted_joins = generator._extract_joins(query)
        
        # Check that the joins were extracted
        self.assertIsNotNone(extracted_joins)
        self.assertIsInstance(extracted_joins, list)
    
    def test_extract_indexes(self):
        """Test that _extract_indexes correctly extracts indexes from a model"""
        # Get the model
        model = TestFilterableModel
        
        # Extract the indexes
        generator = QueryPlanGenerator()
        extracted_indexes = generator._extract_indexes(model)
        
        # Check that the indexes were extracted
        self.assertIsNotNone(extracted_indexes)
        self.assertIsInstance(extracted_indexes, list)

class TestIndexOptimizer(TestCase):
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
        self.model3 = TestFilterableModel.objects.create(
            name="Another", 
            description="Description 3", 
            age=35, 
            is_active=True
        )
    
    def test_index_optimizer_initialization(self):
        """Test that IndexOptimizer initializes correctly"""
        optimizer = IndexOptimizer()
        self.assertIsNotNone(optimizer)
        self.assertIsInstance(optimizer, IndexOptimizer)
    
    def test_optimize_indexes(self):
        """Test that optimize_indexes returns optimized indexes"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Optimize the indexes
        optimizer = IndexOptimizer()
        optimized_indexes = optimizer.optimize_indexes(queryset)
        
        # Check that the optimized indexes are valid
        self.assertIsNotNone(optimized_indexes)
        self.assertIsInstance(optimized_indexes, list)
    
    def test_optimize_indexes_with_complex_filters(self):
        """Test that optimize_indexes works with complex filters"""
        # Create a complex filter
        filters = {
            'name': {'startswith': 'Test', 'contains': '1'},
            'age': {'gt': 20, 'lt': 30},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Optimize the indexes
        optimizer = IndexOptimizer()
        optimized_indexes = optimizer.optimize_indexes(queryset)
        
        # Check that the optimized indexes are valid
        self.assertIsNotNone(optimized_indexes)
        self.assertIsInstance(optimized_indexes, list)
    
    def test_extract_filters(self):
        """Test that _extract_filters correctly extracts filters from a query"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Get the query
        query = queryset.query
        
        # Extract the filters
        optimizer = IndexOptimizer()
        extracted_filters = optimizer._extract_filters(query)
        
        # Check that the filters were extracted
        self.assertIsNotNone(extracted_filters)
        self.assertIsInstance(extracted_filters, dict)
    
    def test_get_model_indexes(self):
        """Test that _get_model_indexes correctly gets indexes from a model"""
        # Get the model
        model = TestFilterableModel
        
        # Get the indexes
        optimizer = IndexOptimizer()
        model_indexes = optimizer._get_model_indexes(model)
        
        # Check that the indexes were retrieved
        self.assertIsNotNone(model_indexes)
        self.assertIsInstance(model_indexes, list)
    
    def test_suggest_indexes(self):
        """Test that _suggest_indexes correctly suggests indexes based on filters"""
        # Create a filter
        filters = {
            'name__startswith': True,
            'is_active': True
        }
        
        # Get the model
        model = TestFilterableModel
        
        # Get the existing indexes
        optimizer = IndexOptimizer()
        existing_indexes = optimizer._get_model_indexes(model)
        
        # Suggest indexes
        suggested_indexes = optimizer._suggest_indexes(filters, existing_indexes)
        
        # Check that the suggested indexes are valid
        self.assertIsNotNone(suggested_indexes)
        self.assertIsInstance(suggested_indexes, list)

class TestJoinOptimizer(TestCase):
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
        self.model3 = TestFilterableModel.objects.create(
            name="Another", 
            description="Description 3", 
            age=35, 
            is_active=True
        )
    
    def test_join_optimizer_initialization(self):
        """Test that JoinOptimizer initializes correctly"""
        optimizer = JoinOptimizer()
        self.assertIsNotNone(optimizer)
        self.assertIsInstance(optimizer, JoinOptimizer)
    
    def test_optimize_joins(self):
        """Test that optimize_joins returns optimized joins"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Optimize the joins
        optimizer = JoinOptimizer()
        optimized_joins = optimizer.optimize_joins(queryset)
        
        # Check that the optimized joins are valid
        self.assertIsNotNone(optimized_joins)
        self.assertIsInstance(optimized_joins, list)
    
    def test_optimize_joins_with_complex_filters(self):
        """Test that optimize_joins works with complex filters"""
        # Create a complex filter
        filters = {
            'name': {'startswith': 'Test', 'contains': '1'},
            'age': {'gt': 20, 'lt': 30},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Optimize the joins
        optimizer = JoinOptimizer()
        optimized_joins = optimizer.optimize_joins(queryset)
        
        # Check that the optimized joins are valid
        self.assertIsNotNone(optimized_joins)
        self.assertIsInstance(optimized_joins, list)
    
    def test_extract_joins(self):
        """Test that _extract_joins correctly extracts joins from a query"""
        # Create a filter
        filters = {
            'name': {'startswith': 'Test'},
            'is_active': True
        }
        
        # Get the queryset
        queryset = TestFilterableModel.filter(filters)
        
        # Get the query
        query = queryset.query
        
        # Extract the joins
        optimizer = JoinOptimizer()
        extracted_joins = optimizer._extract_joins(query)
        
        # Check that the joins were extracted
        self.assertIsNotNone(extracted_joins)
        self.assertIsInstance(extracted_joins, list)
    
    def test_optimize_join_order(self):
        """Test that _optimize_join_order correctly optimizes join order"""
        # Create a list of joins
        joins = [
            {
                'table': 'table1',
                'condition': 'condition1'
            },
            {
                'table': 'table2',
                'condition': 'condition2'
            }
        ]
        
        # Optimize the join order
        optimizer = JoinOptimizer()
        optimized_joins = optimizer._optimize_join_order(joins)
        
        # Check that the optimized joins are valid
        self.assertIsNotNone(optimized_joins)
        self.assertIsInstance(optimized_joins, list)
        self.assertEqual(len(optimized_joins), len(joins)) 