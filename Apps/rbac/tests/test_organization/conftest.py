import pytest
from .factories import OrganizationFactory

@pytest.fixture
def organization_factory():
    """Fixture to provide OrganizationFactory"""
    return OrganizationFactory 