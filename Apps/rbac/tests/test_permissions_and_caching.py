"""
Tests for RBAC permissions and caching.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from ..models import Role, RBACPermission, FieldPermission, RolePermission, UserRole
from ..permissions.caching import (
    get_cached_user_permissions,
    get_cached_field_permissions,
    invalidate_permissions,
    invalidate_field_permissions,
    invalidate_role_permissions,
    invalidate_all_permissions
)
from ..permissions import has_permission, has_field_permission, RBACPermissionMixin

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user."""
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpass')

@pytest.fixture
def test_role(test_user):
    """Create a test role."""
    return Role.objects.create(name='Test Role', created_by=test_user)

@pytest.fixture
def test_content_type():
    """Create a test content type."""
    return ContentType.objects.get_for_model(User)

@pytest.fixture
def test_permission(test_content_type, test_user):
    """Create a test permission."""
    return RBACPermission.objects.create(
        content_type=test_content_type,
        codename='test_permission_1',
        name='Test Permission 1',
        created_by=test_user
    )

@pytest.fixture
def test_field_permission(test_content_type, test_user):
    """Create a test field permission."""
    return FieldPermission.objects.create(
        content_type=test_content_type,
        field_name='username',
        permission_type='read',
        created_by=test_user
    )

@pytest.fixture
def test_role_permission(test_role, test_permission, test_user):
    """Create test role permissions."""
    # Create model permission
    model_permission = RolePermission.objects.create(
        role=test_role,
        permission=test_permission,
        created_by=test_user
    )
    
    return model_permission  # Return the model permission for model permission tests

@pytest.fixture
def test_role_field_permission(test_role, test_field_permission, test_user):
    """Create test role field permissions."""
    # Create role permission with field permission
    role_permission = RolePermission.objects.create(
        role=test_role,
        field_permission=test_field_permission,
        created_by=test_user
    )
    
    return role_permission  # Return the role permission for role permission tests

@pytest.fixture
def test_user_role(test_user, test_role, test_role_permission, test_role_field_permission):
    """Create test user role."""
    return UserRole.objects.create(
        user=test_user,
        role=test_role,
        created_by=test_user
    )

@pytest.mark.django_db
class TestPermissionCaching:
    """Test permission caching functionality."""
    
    def test_get_cached_user_permissions(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test getting cached user permissions."""
        # Get permissions for the first time (should cache)
        permissions = get_cached_user_permissions(test_user, User)
        assert test_permission.codename in permissions

        # Get permissions again (should use cache)
        cached_permissions = get_cached_user_permissions(test_user, User)
        assert cached_permissions == permissions

    def test_get_cached_field_permissions(self, test_user, test_role, test_permission, test_field_permission, test_role_field_permission, test_user_role):
        """Test getting cached field permissions."""
        # Get field permissions for the first time (should cache)
        field_permissions = get_cached_field_permissions(test_user, User)
        assert test_field_permission.field_name in field_permissions
        assert test_field_permission.permission_type in field_permissions[test_field_permission.field_name]

        # Get field permissions again (should use cache)
        cached_field_permissions = get_cached_field_permissions(test_user, User)
        assert cached_field_permissions == field_permissions

    def test_invalidate_permissions(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test invalidating permissions cache."""
        # Get permissions (should cache)
        permissions = get_cached_user_permissions(test_user, User)
        
        # Invalidate permissions
        invalidate_permissions(test_user, User)
        
        # Get permissions again (should not use cache)
        new_permissions = get_cached_user_permissions(test_user, User)
        assert new_permissions == permissions

    def test_invalidate_field_permissions(self, test_user, test_role, test_permission, test_field_permission, test_role_field_permission, test_user_role):
        """Test invalidating field permissions cache."""
        # Get field permissions (should cache)
        field_permissions = get_cached_field_permissions(test_user, User)
        
        # Invalidate field permissions
        invalidate_field_permissions(test_user, User)
        
        # Get field permissions again (should not use cache)
        new_field_permissions = get_cached_field_permissions(test_user, User)
        assert new_field_permissions == field_permissions

    def test_invalidate_role_permissions(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test invalidating role permissions cache."""
        # Get permissions (should cache)
        permissions = get_cached_user_permissions(test_user, User)
        
        # Invalidate role permissions
        invalidate_role_permissions(test_role)
        
        # Get permissions again (should not use cache)
        new_permissions = get_cached_user_permissions(test_user, User)
        assert new_permissions == permissions

    def test_invalidate_all_permissions(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test invalidating all permissions cache."""
        # Get permissions (should cache)
        permissions = get_cached_user_permissions(test_user, User)
        
        # Invalidate all permissions
        invalidate_all_permissions()
        
        # Get permissions again (should not use cache)
        new_permissions = get_cached_user_permissions(test_user, User)
        assert new_permissions == permissions

@pytest.mark.django_db
class TestPermissionDecorators:
    """Test permission decorators."""
    
    def test_has_permission_decorator(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test has_permission decorator."""
        @has_permission('test_permission_1')
        def test_view(request, **kwargs):
            return True
        
        # Test with valid permission
        request = type('Request', (), {'user': test_user})()
        assert test_view(request, model=User) is True
        
        # Test with invalid permission
        test_role_permission.permission.codename = 'invalid_permission'
        test_role_permission.permission.save()
        with pytest.raises(PermissionDenied):
            test_view(request, model=User)

    def test_has_field_permission_decorator(self, test_user, test_role, test_permission, test_field_permission, test_role_field_permission, test_user_role):
        """Test has_field_permission decorator."""
        @has_field_permission('read')
        def test_view(request, **kwargs):
            return True
        
        # Test with valid field permission
        request = type('Request', (), {'user': test_user})()
        assert test_view(request, model=User, field_name='username') is True
        
        # Test with invalid field permission
        test_role_field_permission.field_permission.permission_type = 'invalid'
        test_role_field_permission.field_permission.save()
        with pytest.raises(PermissionDenied):
            test_view(request, model=User, field_name='username')

@pytest.mark.django_db
class TestRBACPermissionMixin:
    """Test RBACPermissionMixin."""
    
    def test_has_permission(self, test_user, test_role, test_permission, test_role_permission, test_user_role):
        """Test has_permission method."""
        class TestView(RBACPermissionMixin):
            def __init__(self, user):
                self.user = user
        
        view = TestView(test_user)
        assert view.has_permission('test_permission_1', User) is True
        
        # Test with invalid permission
        test_role_permission.permission.codename = 'invalid_permission'
        test_role_permission.permission.save()
        assert view.has_permission('test_permission_1', User) is False

    def test_has_field_permission(self, test_user, test_role, test_permission, test_field_permission, test_role_field_permission, test_user_role):
        """Test has_field_permission method."""
        class TestView(RBACPermissionMixin):
            def __init__(self, user):
                self.user = user
                self.model = User
        
        view = TestView(test_user)
        assert view.has_field_permission(test_user, 'username', 'read') is True
        
        # Test with invalid field permission
        test_role_field_permission.field_permission.permission_type = 'invalid'
        test_role_field_permission.field_permission.save()
        assert view.has_field_permission(test_user, 'username', 'read') is False 