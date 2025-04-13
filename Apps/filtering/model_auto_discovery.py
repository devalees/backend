"""
Model Auto-Discovery Integration Helper

This module provides helper functions to automatically discover and register
models for filtering and aggregation capabilities.
"""
from typing import List, Dict, Any, Type, Optional, Tuple
from django.db import models
from django.apps import apps
from .model_discovery import ModelDiscoveryService
from .registry import ModelRegistry, model_registry
from .base import BaseFilterableModel, BaseAggregatableModel
from .auto_mixin_applier import AutoMixinApplier, apply_mixins_to_model, register_model_indexes
from .model_validation import ModelValidator, ValidationResult


def discover_and_register_app_models(app_label: str) -> List[Type[models.Model]]:
    """
    Discover and register models from a specific app.
    
    Args:
        app_label: The label of the Django app
        
    Returns:
        A list of discovered and registered models
    """
    discovery_service = ModelDiscoveryService()
    discovered_models = discovery_service.discover_models_from_app(app_label)
    
    # Register each discovered model
    for model in discovered_models:
        model_registry.register_model(model)
    
    return discovered_models


def discover_and_register_all_models() -> Dict[str, List[Type[models.Model]]]:
    """
    Discover and register models from all installed apps.
    
    Returns:
        A dictionary mapping app labels to lists of discovered and registered models
    """
    discovery_service = ModelDiscoveryService()
    discovered_models_by_app = {}
    
    for app_config in apps.get_app_configs():
        discovered_models = discovery_service.discover_models_from_app(app_config.label)
        if discovered_models:
            discovered_models_by_app[app_config.label] = discovered_models
            # Register each discovered model
            for model in discovered_models:
                model_registry.register_model(model)
    
    return discovered_models_by_app


def generate_model_report(app_label: str = None) -> Dict[str, Any]:
    """
    Generate a detailed report about the discovered models.
    
    Args:
        app_label: Optional app label to limit the report to
        
    Returns:
        A dictionary with detailed information about the discovered models
    """
    discovery_service = ModelDiscoveryService()
    report = {
        'total_models': 0,
        'filterable_models': 0,
        'aggregatable_models': 0,
        'both_capability_models': 0,
        'apps': {},
    }
    
    app_configs = [apps.get_app_config(app_label)] if app_label else apps.get_app_configs()
    
    for app_config in app_configs:
        app_report = {
            'total_models': 0,
            'filterable_models': 0,
            'aggregatable_models': 0,
            'both_capability_models': 0,
            'models': {}
        }
        
        # Get all models from the app
        app_models = discovery_service.discover_models_from_app(app_config.label)
        
        for model in app_models:
            is_filterable = issubclass(model, BaseFilterableModel)
            is_aggregatable = issubclass(model, BaseAggregatableModel)
            
            field_types = discovery_service.detect_field_types(model)
            relationships = discovery_service.map_relationships(model)
            
            app_report['models'][model.__name__] = {
                'is_filterable': is_filterable,
                'is_aggregatable': is_aggregatable,
                'field_count': len(field_types),
                'relationship_count': len(relationships),
                'fields': field_types,
                'relationships': {
                    name: {
                        'type': info['type'],
                        'related_model': info['model'].__name__
                    } for name, info in relationships.items()
                }
            }
            
            # Update counters
            app_report['total_models'] += 1
            if is_filterable:
                app_report['filterable_models'] += 1
            if is_aggregatable:
                app_report['aggregatable_models'] += 1
            if is_filterable and is_aggregatable:
                app_report['both_capability_models'] += 1
        
        # Add app report to overall report
        if app_report['total_models'] > 0:
            report['apps'][app_config.label] = app_report
            report['total_models'] += app_report['total_models']
            report['filterable_models'] += app_report['filterable_models']
            report['aggregatable_models'] += app_report['aggregatable_models']
            report['both_capability_models'] += app_report['both_capability_models']
    
    return report


# New functions for model validation

def validate_models(models: List[Type[models.Model]], detailed: bool = False) -> Dict[str, Any]:
    """
    Validate a list of models for filtering and aggregation compatibility.
    
    Args:
        models: List of models to validate
        detailed: Whether to include detailed validation results
        
    Returns:
        Dictionary with validation summary and optionally detailed results
    """
    validator = ModelValidator()
    validation_results = validator.batch_validate_models(models)
    
    # Count models by validation status
    valid_models = sum(1 for result in validation_results.values() if result.is_valid)
    invalid_models = len(validation_results) - valid_models
    
    # Count issues by severity
    critical_issues = sum(len(result.get_issues_by_severity('critical')) 
                         for result in validation_results.values())
    warning_issues = sum(len(result.get_issues_by_severity('warning')) 
                        for result in validation_results.values())
    info_issues = sum(len(result.get_issues_by_severity('info')) 
                     for result in validation_results.values())
    
    # Create summary
    summary = {
        'total_models': len(models),
        'valid_models': valid_models,
        'invalid_models': invalid_models,
        'critical_issues': critical_issues,
        'warning_issues': warning_issues,
        'info_issues': info_issues
    }
    
    # If detailed results are requested, include them
    if detailed:
        details = {}
        for model_name, result in validation_results.items():
            details[model_name] = {
                'is_valid': result.is_valid,
                'critical_issues': len(result.get_issues_by_severity('critical')),
                'warning_issues': len(result.get_issues_by_severity('warning')),
                'info_issues': len(result.get_issues_by_severity('info')),
                'issues': [
                    {
                        'field': issue.field,
                        'type': issue.issue_type,
                        'message': issue.message,
                        'severity': issue.severity
                    }
                    for issue in result.issues
                ]
            }
        summary['details'] = details
    
    return summary


def validate_app_models(app_label: str, detailed: bool = False) -> Dict[str, Any]:
    """
    Validate all models in a specific app.
    
    Args:
        app_label: The label of the app to validate
        detailed: Whether to include detailed validation results
        
    Returns:
        Dictionary with validation summary
    """
    discovery_service = ModelDiscoveryService()
    models = discovery_service.discover_models_from_app(app_label)
    
    if not models:
        return {
            'total_models': 0,
            'valid_models': 0,
            'invalid_models': 0,
            'critical_issues': 0,
            'warning_issues': 0,
            'info_issues': 0,
            'message': f"No models found in app '{app_label}'"
        }
    
    return validate_models(models, detailed)


def validate_and_enhance_app_models(app_label: str) -> Tuple[List[Type[models.Model]], Dict[str, Any]]:
    """
    Validate models from a specific app and enhance them with mixins.
    
    Args:
        app_label: The label of the Django app
        
    Returns:
        A tuple containing a list of enhanced models and validation summary
    """
    discovery_service = ModelDiscoveryService()
    mixin_applier = AutoMixinApplier(validate=True)
    
    # First discover models
    models = discovery_service.discover_models_from_app(app_label)
    
    # Validate models
    validation_summary = validate_models(models, detailed=True)
    
    # Enhance models (validation happens during enhancement too)
    enhanced_models = mixin_applier.batch_apply_mixins(models)
    
    # Register indexes for all enhanced models
    for model in enhanced_models:
        register_model_indexes(model)
    
    return enhanced_models, validation_summary


# New functions for automatic mixin application

def discover_and_enhance_app_models(app_label: str) -> List[Type[models.Model]]:
    """
    Discover models from a specific app and enhance them with mixins.
    
    Args:
        app_label: The label of the Django app
        
    Returns:
        A list of enhanced models with mixins applied
    """
    mixin_applier = AutoMixinApplier()
    enhanced_models = mixin_applier.discover_and_enhance_app_models(app_label)
    
    # Register indexes for all enhanced models
    for model in enhanced_models:
        register_model_indexes(model)
    
    return enhanced_models


def discover_and_enhance_all_models() -> Dict[str, List[Type[models.Model]]]:
    """
    Discover models from all installed apps and enhance them with mixins.
    
    Returns:
        A dictionary mapping app labels to lists of enhanced models
    """
    mixin_applier = AutoMixinApplier()
    enhanced_models_by_app = mixin_applier.discover_and_enhance_all_models()
    
    # Register indexes for all enhanced models
    for app_label, models_list in enhanced_models_by_app.items():
        for model in models_list:
            register_model_indexes(model)
    
    return enhanced_models_by_app


def enhance_existing_model(model: Type[models.Model]) -> Type[models.Model]:
    """
    Enhance an existing model with mixins.
    
    Args:
        model: The model to enhance
        
    Returns:
        The enhanced model with mixins applied
    """
    enhanced_model = apply_mixins_to_model(model)
    
    # Register the enhanced model
    model_registry.register_model(enhanced_model)
    
    # Register indexes
    register_model_indexes(enhanced_model)
    
    return enhanced_model


def validate_and_enhance_existing_model(model: Type[models.Model]) -> Tuple[Type[models.Model], ValidationResult]:
    """
    Validate an existing model and enhance it with mixins.
    
    Args:
        model: The model to validate and enhance
        
    Returns:
        A tuple containing the enhanced model and validation result
    """
    validator = ModelValidator()
    validation_result = validator.validate_model(model)
    
    # Enhance the model (skipping validation since we already did it)
    enhanced_model = apply_mixins_to_model(model, validate=False)
    
    # Store validation result on the enhanced model
    setattr(enhanced_model, '_validation_result', validation_result)
    
    # Register the enhanced model
    model_registry.register_model(enhanced_model)
    
    # Register indexes
    register_model_indexes(enhanced_model, validate=False)
    
    return enhanced_model, validation_result


def generate_validation_report(app_label: str = None) -> Dict[str, Any]:
    """
    Generate a detailed validation report for all models.
    
    Args:
        app_label: Optional app label to limit the report to
        
    Returns:
        A dictionary with detailed validation information
    """
    validator = ModelValidator()
    return validator.generate_validation_report(app_label) 