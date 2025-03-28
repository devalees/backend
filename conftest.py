import os
import sys
import django
from django.conf import settings

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'Apps'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Apps.core.settings')

# Import pytest fixtures after Django setup
import pytest
from django.test import Client, TransactionTestCase
from django.test.utils import setup_test_environment, teardown_test_environment

def pytest_configure():
    """Configure Django for testing"""
    django.setup()
    setup_test_environment()

def pytest_unconfigure():
    """Clean up test environment"""
    teardown_test_environment()

@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Configure Django database for testing"""
    from django.conf import settings
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }

@pytest.fixture
def client():
    """A Django test client instance"""
    return Client()

@pytest.fixture
def admin_client(client, django_user_model):
    """A Django test client logged in as an admin user"""
    admin_user = django_user_model.objects.create_superuser('admin', 'admin@test.com', 'password')
    client.force_login(admin_user)
    return client

@pytest.fixture
def user_client(client, django_user_model):
    """A Django test client logged in as a regular user"""
    user = django_user_model.objects.create_user('user', 'user@test.com', 'password')
    client.force_login(user)
    return client

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests automatically"""
    pass

@pytest.fixture(scope='function')
def transactional_db(request):
    """Ensure test runs in a transaction that is rolled back"""
    transaction_test_case = TransactionTestCase()
    transaction_test_case._pre_setup()
    request.addfinalizer(transaction_test_case._post_teardown)
    return transaction_test_case 