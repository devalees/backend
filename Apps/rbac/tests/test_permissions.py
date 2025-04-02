"""
Tests for RBAC permissions.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from ..models import RBACPermission, FieldPermission, RolePermission, UserRole, Role
from ..permissions.caching import get_cached_user_permissions, get_cached_field_permissions
from django.db.utils import IntegrityError
from django.test import TestCase

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user."""
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpass')

@pytest.fixture
def test_role():
    """Create a test role."""
    return Role.objects.create(name='Test Role')

@pytest.fixture
def test_content_type():
    """Create a test content type."""
    return ContentType.objects.get_for_model(User)

@pytest.fixture
def test_permission(test_content_type):
    """Create a test permission."""
    return RBACPermission.objects.create(
        content_type=test_content_type,
        codename='test_permission_1',
        name='Test Permission 1'
    )

@pytest.fixture
def test_field_permission(test_content_type):
    """Create a test field permission."""
    return FieldPermission.objects.create(
        content_type=test_content_type,
        field_name='username',
        permission_type='read'
    )

@pytest.fixture
def test_role_permission(test_role, test_permission, test_user):
    """Create test role permissions."""
    return RolePermission.objects.create(
        role=test_role,
        permission=test_permission,
        created_by=test_user
    )

@pytest.fixture
def test_role_field_permission(test_role, test_field_permission, test_user):
    """Create test role field permissions."""
    return RolePermission.objects.create(
        role=test_role,
        field_permission=test_field_permission,
        created_by=test_user
    )

@pytest.fixture
def test_user_role(test_user, test_role, test_role_permission, test_role_field_permission):
    """Create test user role."""
    return UserRole.objects.create(
        user=test_user,
        role=test_role,
        created_by=test_user
    )

class TestRBACPermission(TestCase):
    """Test cases for RBACPermission model."""
    def test_permission_creation(self):
        """Test permission creation."""
        content_type = ContentType.objects.get_for_model(User)
        permission = RBACPermission.objects.create(
            content_type=content_type,
            codename='test_permission',
            name='Test Permission'
        )
        self.assertEqual(permission.codename, 'test_permission')
        self.assertEqual(permission.name, 'Test Permission')
        self.assertEqual(permission.content_type, content_type)

    def test_permission_validation(self):
        """Test permission validation."""
        content_type = ContentType.objects.get_for_model(User)
        permission = RBACPermission(
            content_type=content_type,
            codename='',  # Empty codename
            name='Test Permission'
        )
        with self.assertRaises(ValidationError):
            permission.full_clean()

    def test_permission_unique_constraint(self):
        """Test that permissions must be unique per content type and codename."""
        content_type = ContentType.objects.get_for_model(User)
        RBACPermission.objects.create(
            content_type=content_type,
            codename='test_permission',
            name='Test Permission'
        )
        with self.assertRaises(IntegrityError):
            RBACPermission.objects.create(
                content_type=content_type,
                codename='test_permission',  # Same codename for same content type
                name='Test Permission 2'
            )

class TestFieldPermission(TestCase):
    """Test cases for FieldPermission model."""
    def test_field_permission_creation(self):
        """Test field permission creation."""
        content_type = ContentType.objects.get_for_model(User)
        field_permission = FieldPermission.objects.create(
            content_type=content_type,
            field_name='username',
            permission_type='read'
        )
        self.assertEqual(field_permission.field_name, 'username')
        self.assertEqual(field_permission.permission_type, 'read')
        self.assertEqual(field_permission.content_type, content_type)

    def test_field_permission_validation(self):
        """Test field permission validation."""
        content_type = ContentType.objects.get_for_model(User)
        field_permission = FieldPermission(
            content_type=content_type,
            field_name='',  # Empty field name
            permission_type='read'
        )
        with self.assertRaises(ValidationError):
            field_permission.full_clean()

    def test_field_permission_unique_constraint(self):
        """Test that field permissions must be unique per content type, field name, and permission type."""
        content_type = ContentType.objects.get_for_model(User)
        FieldPermission.objects.create(
            content_type=content_type,
            field_name='username',
            permission_type='read'
        )
        with self.assertRaises(IntegrityError):
            FieldPermission.objects.create(
                content_type=content_type,
                field_name='username',  # Same field name
                permission_type='read'  # Same permission type
            )

class TestRolePermission(TestCase):
    """Test cases for RolePermission model."""
    
    def setUp(self):
        """Set up test data."""
        self.content_type = ContentType.objects.get_for_model(User)
        self.role = Role.objects.create(name='Test Role')
        self.permission = RBACPermission.objects.create(
            content_type=self.content_type,
            codename='test_permission',
            name='Test Permission'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        self.user_role = UserRole.objects.create(user=self.user, role=self.role)

    def test_role_permission_creation(self):
        """Test role permission creation."""
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        self.assertEqual(role_permission.role, self.role)
        self.assertEqual(role_permission.permission, self.permission)
        self.assertIsNone(role_permission.field_permission)

    def test_role_permission_validation(self):
        """Test role permission validation."""
        field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='read'
        )
        
        # Test that we can't create a role permission with both permission and field_permission
        role_permission = RolePermission(
            role=self.role,
            permission=self.permission,
            field_permission=field_permission
        )
        with self.assertRaises(ValidationError):
            role_permission.full_clean()

        # Test that we can't create a role permission without either permission or field_permission
        role_permission = RolePermission(role=self.role)
        with self.assertRaises(ValidationError):
            role_permission.full_clean()

    def test_role_permission_unique_constraint(self):
        """Test that role permissions must be unique per role and permission."""
        RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )
        
        with self.assertRaises(IntegrityError):
            RolePermission.objects.create(
                role=self.role,
                permission=self.permission  # Same role and permission
            )

    def test_cache_invalidation_on_permission_change(self):
        """Test that user permissions cache is invalidated when role permissions change."""
        # Create initial role permission
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission
        )

        # Get initial cached permissions
        initial_permissions = get_cached_user_permissions(self.user, User)
        self.assertIn(self.permission.codename, initial_permissions)

        # Delete role permission
        role_permission.delete()

        # Check that cache is invalidated
        updated_permissions = get_cached_user_permissions(self.user, User)
        self.assertNotIn(self.permission.codename, updated_permissions)

    def test_cache_invalidation_on_role_permission_change(self):
        """Test that field permissions cache is invalidated when role permissions change."""
        # Create field permission
        field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='read'
        )

        # Create role permission with field permission
        role_permission = RolePermission.objects.create(
            role=self.role,
            field_permission=field_permission
        )

        # Get initial cached field permissions
        initial_field_permissions = get_cached_field_permissions(self.user, User)
        self.assertIn('username', initial_field_permissions)
        self.assertIn('read', initial_field_permissions['username'])

        # Delete role permission
        role_permission.delete()

        # Check that cache is invalidated
        updated_field_permissions = get_cached_field_permissions(self.user, User)
        self.assertNotIn('username', updated_field_permissions)

class TestUserRole(TestCase):
    """Test cases for UserRole model."""
    def test_user_role_creation(self):
        """Test user role creation."""
        user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        role = Role.objects.create(name='Test Role')
        user_role = UserRole.objects.create(
            user=user,
            role=role
        )
        self.assertEqual(user_role.user, user)
        self.assertEqual(user_role.role, role)
        self.assertTrue(user_role.is_active)

    def test_user_role_unique_constraint(self):
        """Test that user roles must be unique per user and role."""
        user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        role = Role.objects.create(name='Test Role')
        
        UserRole.objects.create(
            user=user,
            role=role
        )
        
        with self.assertRaises(IntegrityError):
            UserRole.objects.create(
                user=user,
                role=role  # Same user and role
            )

@pytest.mark.django_db
class TestPermissionCaching:
    """Test permission caching."""
    
    def test_get_cached_user_permissions(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test getting cached user permissions."""
        # Get permissions for the first time (should cache)
        permissions = get_cached_user_permissions(test_user, User)
        assert test_permission.codename in permissions

        # Get permissions again (should use cache)
        cached_permissions = get_cached_user_permissions(test_user, User)
        assert cached_permissions == permissions

    def test_get_cached_field_permissions(self, test_user, test_role, test_permission, test_field_permission, test_role_permission, test_user_role):
        """Test getting cached field permissions."""
        # Get field permissions for the first time (should cache)
        field_permissions = get_cached_field_permissions(test_user, User)
        assert test_field_permission.field_name in field_permissions
        assert test_field_permission.permission_type in field_permissions[test_field_permission.field_name]

        # Get field permissions again (should use cache)
        cached_field_permissions = get_cached_field_permissions(test_user, User)
        assert cached_field_permissions == field_permissions 