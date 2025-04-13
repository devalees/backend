"""
pytest configuration file for Django integration.
This file configures pytest to work with Django and provides fixtures for testing.
"""
import os
import sys
import pytest
import django
from django.conf import settings
from django.apps import apps

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Configure Django settings for testing
def pytest_configure():
    # Define test settings if Django is not configured
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=True,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.admin",
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "django.contrib.staticfiles",
                "Apps.filtering",
            ],
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ],
            ROOT_URLCONF="",
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.debug",
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                    },
                },
            ],
            SECRET_KEY="test_secret_key",
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )
        
        # Initialize Django
        django.setup()
        
        # Create the filtering app
        if not apps.is_installed("Apps.filtering"):
            app_config = apps.get_app_config("filtering")
            app_config.import_models()
            
    return settings

@pytest.fixture
def discovery_service():
    """Provide a model discovery service fixture for tests."""
    from Apps.filtering.model_discovery import ModelDiscoveryService
    return ModelDiscoveryService() 