import pytest
from django.core.exceptions import ValidationError
from Apps.rbac.models import Role
from Apps.entity.models import Organization
from Apps.users.models import User

@pytest.mark.django_db
class TestRoleModel:
    """Test cases for the Role model"""

    @pytest.fixture(autouse=True)
    def setup(self, organization, user):
        """Set up test data"""
        self.organization = organization
        self.parent_role = Role.objects.create(
            name="Parent Role",
            description="Parent role for testing",
            organization=self.organization
        )
        self.user = user

    def test_role_creation(self):
        """Test basic role creation"""
        role = Role.objects.create(
            name="Test Role",
            description="Test role description",
            organization=self.organization
        )
        assert role.name == "Test Role"
        assert role.description == "Test role description"
        assert role.organization == self.organization
        assert role.is_active is True
        assert role.created_at is not None
        assert role.updated_at is not None

    def test_role_hierarchy(self):
        """Test role hierarchy relationships"""
        child_role = Role.objects.create(
            name="Child Role",
            description="Child role for testing",
            organization=self.organization,
            parent=self.parent_role
        )
        assert child_role.parent == self.parent_role
        assert child_role in self.parent_role.children.all()

    def test_role_name_validation(self):
        """Test role name validation"""
        # Test empty name
        with pytest.raises(ValidationError):
            Role.objects.create(
                name="",
                description="Test role",
                organization=self.organization
            )

        # Test name with special characters
        with pytest.raises(ValidationError):
            Role.objects.create(
                name="Test@Role",
                description="Test role",
                organization=self.organization
            )

    def test_role_organization_required(self):
        """Test that organization is required"""
        with pytest.raises(ValidationError):
            Role.objects.create(
                name="Test Role",
                description="Test role"
            )

    def test_role_permissions(self, common_permissions):
        """Test role permission methods"""
        role = Role.objects.create(
            name="Test Role",
            description="Test role",
            organization=self.organization
        )
        
        # Test adding permission
        role.permissions.add(common_permissions['view_project'])
        assert role.has_permission("view_project") is True
        
        # Test removing permission
        role.permissions.remove(common_permissions['view_project'])
        assert role.has_permission("view_project") is False

    def test_role_inheritance(self, common_permissions):
        """Test role permission inheritance"""
        parent_role = Role.objects.create(
            name="Parent Role 2",
            description="Parent role",
            organization=self.organization
        )
        parent_role.permissions.add(common_permissions['view_project'])
        
        child_role = Role.objects.create(
            name="Child Role",
            description="Child role",
            organization=self.organization,
            parent=parent_role
        )
        
        assert child_role.has_permission("view_project") is True

    def test_role_deactivation(self):
        """Test role deactivation"""
        role = Role.objects.create(
            name="Test Role",
            description="Test role",
            organization=self.organization
        )
        
        role.deactivate()
        assert role.is_active is False
        
        role.activate()
        assert role.is_active is True

    def test_role_cache_invalidation(self, common_permissions):
        """Test role cache invalidation"""
        role = Role.objects.create(
            name="Test Role",
            description="Test role",
            organization=self.organization
        )
        
        # Add permission and check cache
        role.permissions.add(common_permissions['view_project'])
        assert role.has_permission("view_project") is True
        
        # Remove permission and verify cache is invalidated
        role.permissions.remove(common_permissions['view_project'])
        assert role.has_permission("view_project") is False

    def test_role_str_representation(self):
        """Test role string representation"""
        role = Role.objects.create(
            name="Test Role",
            description="Test role",
            organization=self.organization
        )
        assert str(role) == "Test Role" 