from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from ..models import RBACPermission, FieldPermission, Role, RolePermission, UserRole
from ..permissions.checker import has_permission, get_user_permissions, get_field_permissions

User = get_user_model()

class PermissionCachingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.role = Role.objects.create(name='Test Role', created_by=self.user)
        self.permission = RBACPermission.objects.create(
            content_type=self.content_type,
            codename='view_user',
            name='Can view user',
            created_by=self.user
        )
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
            created_by=self.user
        )
        self.role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )
        self.user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.user
        )
        cache.clear()

    def test_permission_caching(self):
        # First call should hit the database
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertTrue(has_perm)

        # Second call should hit the cache
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertTrue(has_perm)

    def test_user_permissions_caching(self):
        # First call should hit the database
        perms = get_user_permissions(self.user, User)
        self.assertIn('view_user', perms)

        # Second call should hit the cache
        perms = get_user_permissions(self.user, User)
        self.assertIn('view_user', perms)

    def test_field_permissions_caching(self):
        # First call should hit the database
        field_perms = get_field_permissions(self.user, User)
        self.assertIn('username', field_perms)

        # Second call should hit the cache
        field_perms = get_field_permissions(self.user, User)
        self.assertIn('username', field_perms)

    def test_cache_invalidation_on_role_permission_change(self):
        # First call to cache the permission
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertTrue(has_perm)

        # Delete the role permission
        self.role_permission.delete()

        # Permission should be rechecked and return False
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertFalse(has_perm)

    def test_cache_invalidation_on_user_role_change(self):
        # First call to cache the permission
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertTrue(has_perm)

        # Delete the user role
        self.user_role.delete()

        # Permission should be rechecked and return False
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertFalse(has_perm)

    def test_cache_invalidation_on_permission_change(self):
        # First call to cache the permission
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertTrue(has_perm)

        # Update the permission
        self.permission.codename = 'new_view_user'
        self.permission.save()

        # Permission should be rechecked and return False
        has_perm = has_permission(self.user, 'view_user', User)
        self.assertFalse(has_perm) 