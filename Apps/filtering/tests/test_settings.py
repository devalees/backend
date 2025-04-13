from django.test.utils import setup_test_environment

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'Apps.core',
    'Apps.entity',
    'Apps.filtering',
]

SECRET_KEY = 'test-key-not-for-production'

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 