#!/usr/bin/env python
"""
Script to apply filtering and aggregation functionality to existing models.

This script discovers existing models in specified Django apps and applies
filtering and aggregation functionality to them using the model registry.

Usage:
    python apply_to_existing_models.py [app_labels...]
    
    If no app labels are provided, all installed apps will be scanned.
"""

import sys
import os
import logging
import django
from django.apps import apps

# Set up Django environment
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from Apps.filtering.model_registry import model_registry


def apply_to_apps(app_labels=None):
    """
    Apply filtering and aggregation to models in specified apps.
    
    Args:
        app_labels: Optional list of app labels to apply to. If None, applies to all apps.
    """
    # Discover models in apps
    discovered = model_registry.discover_models(app_labels)
    logger.info(f"Discovered {len(discovered)} models in {len(app_labels) if app_labels else 'all'} apps")
    
    # Register discovered models
    model_registry.register_discovered_models()
    logger.info(f"Registered {len(model_registry.registered_models)} models with filtering and aggregation")
    
    # Return a summary of registered models by app
    summary = {}
    for model_class in model_registry.registered_models:
        app_label = model_class._meta.app_label
        if app_label not in summary:
            summary[app_label] = []
        summary[app_label].append(model_class.__name__)
    
    return summary


def print_summary(summary):
    """Print a summary of registered models by app."""
    logger.info("Registration Summary:")
    for app_label, model_names in summary.items():
        logger.info(f"  {app_label}: {len(model_names)} models")
        for model_name in sorted(model_names):
            logger.info(f"    - {model_name}")


def main():
    """Main entry point for the script."""
    # Get app labels from command line arguments
    app_labels = sys.argv[1:] if len(sys.argv) > 1 else None
    
    try:
        # Apply filtering and aggregation to models
        summary = apply_to_apps(app_labels)
        
        # Print summary
        print_summary(summary)
        
        logger.info("Successfully applied filtering and aggregation to existing models")
        return 0
    
    except Exception as e:
        logger.error(f"Error applying filtering and aggregation: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main()) 