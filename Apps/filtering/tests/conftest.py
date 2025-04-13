"""
pytest configuration file for Django integration.
This file configures pytest to work with Django and provides fixtures for testing.
"""
import os
import pytest
import django
from django.conf import settings

# Set up Django settings for tests
def pytest_configure():
    """Configure Django for pytest."""
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Apps.filtering.tests.test_settings')
        django.setup()

@pytest.fixture
def discovery_service():
    """Provide a model discovery service fixture for tests."""
    from Apps.filtering.model_discovery import ModelDiscoveryService
    return ModelDiscoveryService() 