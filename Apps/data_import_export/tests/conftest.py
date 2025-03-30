import pytest
from rest_framework.test import APIClient
from .factories import UserFactory, ImportExportConfigFactory
import sys


@pytest.fixture
def ensure_pytest_in_modules():
    """Ensure pytest is in sys.modules."""
    sys.modules['pytest'] = pytest
    yield
    if 'pytest' in sys.modules:
        del sys.modules['pytest']


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Fixture for authenticated API client."""
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture
def test_password():
    """Fixture for test password."""
    return 'test_password123'


@pytest.fixture
def create_user(test_password):
    """Fixture to create a user."""
    def make_user(**kwargs):
        kwargs['password'] = test_password
        if 'username' not in kwargs:
            kwargs['username'] = 'testuser'
        return UserFactory(**kwargs)
    return make_user


@pytest.fixture
def config():
    """Fixture for ImportExportConfig."""
    return ImportExportConfigFactory() 