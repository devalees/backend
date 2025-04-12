from .settings import *

# Exclude problematic apps for testing
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'Apps.documents']

# Add test-specific settings
ELASTICSEARCH_USERNAME = 'test'
ELASTICSEARCH_PASSWORD = 'test' 