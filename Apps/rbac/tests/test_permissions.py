from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from ..models import Role, Permission, FieldPermission, RolePermission, UserRole
from ..permissions import IsAdminOrReadOnly, CanManageRoles

User = get_user_model()

class MockView(APIView):
    pass

class IsAdminOrReadOnlyTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = MockView()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com'
        )

    def test_allow_read_for_authenticated_user(self):
        request = self.factory.get('/')
        request.user = self.user
        permission = IsAdminOrReadOnly()
        self.assertTrue(permission.has_permission(request, self.view))

    def test_deny_read_for_unauthenticated_user(self):
        request = self.factory.get('/')
        request.user = None
        permission = IsAdminOrReadOnly()
        self.assertFalse(permission.has_permission(request, self.view))

    def test_allow_write_for_admin(self):
        request = self.factory.post('/')
        request.user = self.admin
        permission = IsAdminOrReadOnly()
        self.assertTrue(permission.has_permission(request, self.view))

    def test_deny_write_for_non_admin(self):
        request = self.factory.post('/')
        request.user = self.user
        permission = IsAdminOrReadOnly()
        self.assertFalse(permission.has_permission(request, self.view))

class CanManageRolesTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = MockView()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com'
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.admin,
            updated_by=self.admin
        )
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='test_permission',
            created_by=self.admin,
            updated_by=self.admin
        )
        self.content_type = ContentType.objects.create(
            app_label='rbac',
            model='testmodel'
        )
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='test_field',
            permission_type='read',
            created_by=self.admin
        )

    def test_allow_all_for_admin(self):
        request = self.factory.get('/')
        request.user = self.admin
        permission = CanManageRoles()
        self.assertTrue(permission.has_permission(request, self.view))

    def test_deny_all_for_unauthenticated_user(self):
        request = self.factory.get('/')
        request.user = None
        permission = CanManageRoles()
        self.assertFalse(permission.has_permission(request, self.view))

    def test_allow_read_for_user_with_role(self):
        request = self.factory.get('/')
        request.user = self.user
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        permission = CanManageRoles()
        self.assertTrue(permission.has_permission(request, self.view))

    def test_deny_read_for_user_without_role(self):
        request = self.factory.get('/')
        request.user = self.user
        permission = CanManageRoles()
        self.assertFalse(permission.has_permission(request, self.view))

    def test_allow_write_for_user_with_admin_role(self):
        request = self.factory.post('/')
        request.user = self.user
        admin_role = Role.objects.create(
            name='admin',
            created_by=self.admin,
            updated_by=self.admin
        )
        UserRole.objects.create(
            user=self.user,
            role=admin_role,
            created_by=self.admin
        )
        permission = CanManageRoles()
        self.assertTrue(permission.has_permission(request, self.view))

    def test_deny_write_for_user_without_admin_role(self):
        request = self.factory.post('/')
        request.user = self.user
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        permission = CanManageRoles()
        self.assertFalse(permission.has_permission(request, self.view))

    def test_object_permission_for_user(self):
        request = self.factory.get('/')
        request.user = self.user
        permission = CanManageRoles()
        self.assertTrue(permission.has_object_permission(request, self.view, self.user))

    def test_object_permission_for_other_user(self):
        request = self.factory.get('/')
        request.user = self.user
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com'
        )
        permission = CanManageRoles()
        self.assertFalse(permission.has_object_permission(request, self.view, other_user))

    def test_object_permission_for_admin(self):
        request = self.factory.get('/')
        request.user = self.admin
        other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com'
        )
        permission = CanManageRoles()
        self.assertTrue(permission.has_object_permission(request, self.view, other_user)) 