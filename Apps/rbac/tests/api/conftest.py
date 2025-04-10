import pytest
from Apps.rbac.models import Resource

@pytest.fixture
def test_resource(organization):
    """Create a test resource"""
    return Resource.objects.create(
        name="Test Resource",
        resource_type="document",
        organization=organization
    )

@pytest.fixture
def test_user(user):
    """Alias for user fixture to match test naming convention"""
    return user 