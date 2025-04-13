#!/usr/bin/env python3
"""
Simple test runner for manually testing the model discovery implementation.
This script doesn't require pytest or Django test runner.
"""
import os
import sys
import traceback
import importlib

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

try:
    # Import the required classes
    from Apps.filtering.base import BaseFilterableModel, BaseAggregatableModel
    from Apps.filtering.model_discovery import ModelDiscoveryService
    
    print("Successfully imported the model discovery module.")
    
    # Create the discovery service
    discovery_service = ModelDiscoveryService()
    print("Successfully created the model discovery service.")
    
    # Define some test models for demonstration
    from django.db import models
    
    class TestModelA(BaseFilterableModel, BaseAggregatableModel):
        name = models.CharField(max_length=100)
        value = models.IntegerField()
        
        class Meta:
            app_label = 'filtering'
    
    class TestModelB(BaseFilterableModel):
        name = models.CharField(max_length=100)
        related = models.ForeignKey(TestModelA, on_delete=models.CASCADE)
        
        class Meta:
            app_label = 'filtering'
    
    print("Successfully defined test models.")
    
    # Test field detection
    field_types = discovery_service.detect_field_types(TestModelA)
    print(f"Detected field types for TestModelA: {field_types}")
    assert 'name' in field_types
    assert field_types['name'] == 'char'
    assert 'value' in field_types
    assert field_types['value'] == 'integer'
    
    # Test relationship mapping
    relationships = discovery_service.map_relationships(TestModelB)
    print(f"Mapped relationships for TestModelB: {relationships}")
    assert 'related' in relationships
    assert relationships['related']['type'] == 'foreignkey'
    assert relationships['related']['model'] == TestModelA
    
    print("All tests passed successfully! The implementation works as expected.")
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

sys.exit(0) 