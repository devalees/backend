import pytest
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..models import Resource, ResourceAccess
from Apps.entity.models import Organization

User = get_user_model()

@pytest.mark.django_db
class TestResourceAccessModel:
    """Test suite for ResourceAccess model functionality"""

    def test_resource_access_creation(self, organization, user):
        """Test that a resource access can be created with valid data"""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Create resource access
        resource_access = ResourceAccess.objects.create(
            resource=resource,
            user=user,
            access_type="read",
            organization=organization
        )
        
        assert resource_access.resource == resource
        assert resource_access.user == user
        assert resource_access.access_type == "read"
        assert resource_access.organization == organization
        assert resource_access.is_active is True
        assert resource_access.created_at is not None
        assert resource_access.updated_at is not None

    def test_resource_access_validation(self, organization, user):
        """Test that resource access validation works correctly"""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Test with invalid access type
        with pytest.raises(ValidationError):
            resource_access = ResourceAccess.objects.create(
                resource=resource,
                user=user,
                access_type="invalid_type",
                organization=organization
            )
            resource_access.full_clean()

    def test_resource_access_unique_constraint(self, organization, user):
        """Test that resource access unique constraint works correctly"""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Create first resource access
        ResourceAccess.objects.create(
            resource=resource,
            user=user,
            access_type="read",
            organization=organization
        )
        
        # Try to create another resource access with the same resource, user, and access type
        with pytest.raises(ValidationError):
            resource_access = ResourceAccess(
                resource=resource,
                user=user,
                access_type="read",
                organization=organization
            )
            resource_access.full_clean()
            resource_access.save()

    def test_resource_access_deactivation(self, organization, user):
        """Test that a resource access can be deactivated"""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Create resource access
        resource_access = ResourceAccess.objects.create(
            resource=resource,
            user=user,
            access_type="read",
            organization=organization
        )
        
        # Deactivate resource access
        resource_access.deactivate()
        
        assert resource_access.is_active is False
        assert resource_access.deactivated_at is not None

    def test_resource_access_activation(self, organization, user):
        """Test that a resource access can be activated"""
        # Create a resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Create resource access
        resource_access = ResourceAccess.objects.create(
            resource=resource,
            user=user,
            access_type="read",
            organization=organization
        )
        
        # Deactivate resource access
        resource_access.deactivate()
        
        # Activate resource access
        resource_access.activate()
        
        assert resource_access.is_active is True
        assert resource_access.deactivated_at is None 