"""Test settings module for unit tests."""

from django.test.utils import setup_test_environment

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Apps.filtering',
]

SECRET_KEY = 'fake-key'

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Add model_discovery module to coverage reports
# This is important for pytest to track coverage
PYTEST_MODULES_TO_COVER = [
    'Apps.filtering.base',
    'Apps.filtering.registry',
    'Apps.filtering.model_discovery',
] 