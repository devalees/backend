import pytest
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..models import Resource, RBACBaseModel
from Apps.entity.models import Organization

User = get_user_model()

@pytest.mark.django_db
class TestResourceModel:
    """Test suite for Resource model functionality"""

    def test_resource_creation(self, organization):
        """Test that a resource can be created with valid data"""
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        assert resource.name == "Test Resource"
        assert resource.resource_type == "document"
        assert resource.organization == organization
        assert resource.is_active is True
        assert resource.created_at is not None
        assert resource.updated_at is not None

    def test_resource_str_representation(self, organization):
        """Test the string representation of a resource"""
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        assert str(resource) == "Test Resource (document)"

    def test_resource_validation(self, organization):
        """Test that resource validation works correctly"""
        # Test with invalid resource type
        with pytest.raises(ValidationError):
            resource = Resource.objects.create(
                name="Test Resource",
                resource_type="invalid_type",
                organization=organization
            )
            resource.full_clean()

    def test_resource_ownership(self, organization, user):
        """Test that a resource can be assigned an owner"""
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization,
            owner=user
        )
        
        assert resource.owner == user

    def test_resource_inheritance(self, organization):
        """Test that a resource can inherit from another resource"""
        parent_resource = Resource.objects.create(
            name="Parent Resource",
            resource_type="folder",
            organization=organization
        )
        
        child_resource = Resource.objects.create(
            name="Child Resource",
            resource_type="document",
            organization=organization,
            parent=parent_resource
        )
        
        assert child_resource.parent == parent_resource
        assert parent_resource in child_resource.get_ancestors()
        assert child_resource in parent_resource.get_descendants()

    def test_resource_access_control(self, organization, user, role):
        """Test that resource access control works correctly"""
        from ..models import UserRole, Permission
        
        # Create a permission
        permission = Permission.objects.create(
            name="Access Resource",
            code="access_resource",
            organization=organization
        )
        
        # Assign permission to role
        role.permissions.add(permission)
        
        # Create user role
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        
        # Create resource
        resource = Resource.objects.create(
            name="Test Resource",
            resource_type="document",
            organization=organization
        )
        
        # Grant access to user
        resource.grant_access(user, "read")
        
        # Check if user has access
        assert resource.has_access(user, "read") is True
        assert resource.has_access(user, "write") is False 