import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Permission, Role
from Apps.entity.models import Organization

@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Organization")

@pytest.mark.django_db
class TestPermissionModel:
    def test_create_permission(self, organization):
        """Test creating a basic permission"""
        permission = Permission.objects.create(
            name="view_project",
            description="Can view project details",
            code="project.view",
            organization=organization
        )
        assert permission.name == "view_project"
        assert permission.description == "Can view project details"
        assert permission.code == "project.view"
        assert permission.is_active is True
        assert permission.organization == organization

    def test_permission_unique_code(self, organization):
        """Test that permission codes must be unique within an organization"""
        Permission.objects.create(
            name="view_project",
            description="Can view project details",
            code="project.view",
            organization=organization
        )
        with pytest.raises(IntegrityError):
            Permission.objects.create(
                name="view_project_2",
                description="Can view project details",
                code="project.view",
                organization=organization
            )

    def test_permission_name_validation(self, organization):
        """Test permission name validation"""
        with pytest.raises(ValidationError):
            permission = Permission(
                name="",  # Empty name
                description="Invalid permission",
                code="invalid",
                organization=organization
            )
            permission.full_clean()

    def test_permission_code_validation(self, organization):
        """Test permission code validation"""
        with pytest.raises(ValidationError):
            permission = Permission(
                name="test_permission",
                description="Test permission",
                code="invalid code",  # Invalid code format
                organization=organization
            )
            permission.full_clean()

    def test_permission_inheritance(self, organization):
        """Test permission inheritance from RBACBaseModel"""
        permission = Permission.objects.create(
            name="test_permission",
            description="Test permission",
            code="test.permission",
            organization=organization
        )
        assert hasattr(permission, 'created_at')
        assert hasattr(permission, 'updated_at')
        assert hasattr(permission, 'is_active')

    def test_permission_str_representation(self, organization):
        """Test string representation of permission"""
        permission = Permission.objects.create(
            name="test_permission",
            description="Test permission",
            code="test.permission",
            organization=organization
        )
        assert str(permission) == "test_permission"

    def test_permission_deactivation(self, organization):
        """Test deactivating a permission"""
        permission = Permission.objects.create(
            name="test_permission",
            description="Test permission",
            code="test.permission",
            organization=organization
        )
        permission.is_active = False
        permission.save()
        assert not permission.is_active

    def test_permission_with_organization(self, organization):
        """Test creating permission with organization context"""
        permission = Permission.objects.create(
            name="org_permission",
            description="Organization permission",
            code="org.permission",
            organization=organization
        )
        assert permission.organization == organization

    def test_permission_cache_key(self, organization):
        """Test permission cache key generation"""
        permission = Permission.objects.create(
            name="cache_permission",
            description="Cache test permission",
            code="cache.permission",
            organization=organization
        )
        expected_key = f"permission:{permission.id}:{permission.code}"
        assert permission.get_cache_key() == expected_key

    def test_permission_permissions_self(self, organization):
        """Test permission's own permissions"""
        permission = Permission.objects.create(
            name="self_permission",
            description="Self permission test",
            code="self.permission",
            organization=organization
        )
        assert permission.has_permission(permission, 'view')
        assert permission.has_permission(permission, 'change')
        assert permission.has_permission(permission, 'delete')

    def test_same_code_different_organizations(self):
        """Test that same permission code can be used in different organizations"""
        org1 = Organization.objects.create(name="Organization 1")
        org2 = Organization.objects.create(name="Organization 2")

        perm1 = Permission.objects.create(
            name="test_permission",
            description="Test permission",
            code="test.permission",
            organization=org1
        )

        perm2 = Permission.objects.create(
            name="test_permission",
            description="Test permission",
            code="test.permission",
            organization=org2
        )

        assert perm1.code == perm2.code
        assert perm1.organization != perm2.organization 