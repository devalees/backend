import pytest
from Apps.rbac.models import Resource, OrganizationContext

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

@pytest.fixture
def organization_context(organization):
    """Create a test organization context"""
    return OrganizationContext.objects.create(
        name="Test Context",
        description="Test organization context",
        organization=organization
    )

@pytest.fixture
def parent_organization_context(organization):
    """Create a parent test organization context"""
    return OrganizationContext.objects.create(
        name="Parent Context",
        description="Parent organization context",
        organization=organization
    )

@pytest.fixture
def child_organization_context(organization, parent_organization_context):
    """Create a child test organization context"""
    return OrganizationContext.objects.create(
        name="Child Context",
        description="Child organization context",
        organization=organization,
        parent=parent_organization_context
    ) 