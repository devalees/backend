import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def test_organization():
    """Create a test organization"""
    # This will be replaced with actual Organization model when implemented
    return {'id': 1, 'name': 'Test Organization'}

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test"""
    cache.clear() 