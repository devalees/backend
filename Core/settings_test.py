from .settings import *

# Use in-memory SQLite database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use faster password hasher during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable celery tasks during tests
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Disable throttling during tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {}
}

# Use a memory cache backend for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Disable CSRF validation in tests
MIDDLEWARE = [m for m in MIDDLEWARE if 'csrf' not in m.lower()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'import_export',  # Django Import Export base package
    'django_celery_results',  # Celery results backend
    'django_celery_beat',  # Celery beat scheduler
    'Core',  # Core app
    'Apps.core',
    'Apps.users',
    'Apps.entity',
    'Apps.contacts',
    'Apps.data_transfer',
    'Apps.project',
    'Apps.rbac.apps.RbacConfig',  # Use the new app config
    'Apps.time_management',  # Time Management and Timesheet
    'Apps.data_import_export',  # Add the data import/export app
    'Apps.documents',  # Document Management System
]