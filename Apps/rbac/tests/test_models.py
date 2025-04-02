"""
Tests for RBAC models.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from ..models import Role, RBACPermission, FieldPermission, RolePermission, UserRole

User = get_user_model()

@pytest.mark.django_db
class RoleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(
            name='Test Role', 
            description='Test Description',
            created_by=self.user
        )

    def test_role_creation(self):
        self.assertEqual(self.role.name, 'Test Role')
        self.assertEqual(self.role.description, 'Test Description')
        self.assertEqual(self.role.created_by, self.user)

    def test_role_str(self):
        self.assertEqual(str(self.role), 'Test Role')

    def test_role_validation(self):
        role = Role(name='', description='Invalid Role', created_by=self.user)
        with self.assertRaises(ValidationError):
            role.clean()

@pytest.mark.django_db
class RBACPermissionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = RBACPermission.objects.create(
            content_type=self.content_type,
            codename='test_permission',
            name='Test Permission',
            created_by=self.user
        )

    def test_permission_creation(self):
        self.assertEqual(self.permission.codename, 'test_permission')
        self.assertEqual(self.permission.name, 'Test Permission')
        self.assertEqual(self.permission.content_type, self.content_type)
        self.assertEqual(self.permission.created_by, self.user)

    def test_permission_str(self):
        expected = f"{self.permission.name} ({self.permission.content_type.model})"
        self.assertEqual(str(self.permission), expected)

    def test_permission_validation(self):
        with self.assertRaises(ValidationError):
            RBACPermission.objects.create(
                content_type=self.content_type,
                codename='',
                name='',
                created_by=self.user
            )

@pytest.mark.django_db
class FieldPermissionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
            created_by=self.user
        )

    def test_field_permission_creation(self):
        self.assertEqual(self.field_permission.field_name, 'username')
        self.assertEqual(self.field_permission.permission_type, 'view')
        self.assertEqual(self.field_permission.content_type, self.content_type)
        self.assertEqual(self.field_permission.created_by, self.user)

    def test_field_permission_str(self):
        expected = f"{self.field_permission.permission_type} {self.field_permission.field_name} ({self.field_permission.content_type.model})"
        self.assertEqual(str(self.field_permission), expected)

    def test_field_permission_validation(self):
        with self.assertRaises(ValidationError):
            FieldPermission.objects.create(
                content_type=self.content_type,
                field_name='',
                permission_type='',
                created_by=self.user
            )

@pytest.mark.django_db
class RolePermissionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(name='Test Role', created_by=self.user)
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = RBACPermission.objects.create(
            content_type=self.content_type,
            codename='test_permission',
            name='Test Permission',
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

    def test_role_permission_creation(self):
        self.assertEqual(self.role_permission.role, self.role)
        self.assertEqual(self.role_permission.permission, self.permission)
        self.assertIsNone(self.role_permission.field_permission)
        self.assertEqual(self.role_permission.created_by, self.user)

    def test_role_permission_str(self):
        expected = f"{self.role} - {self.permission}"
        self.assertEqual(str(self.role_permission), expected)

    def test_role_permission_validation(self):
        with self.assertRaises(ValidationError):
            RolePermission.objects.create(role=None, permission=None, created_by=self.user)

@pytest.mark.django_db
class UserRoleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(name='Test Role', created_by=self.user)
        self.user_role = UserRole.objects.create(
            user=self.user, 
            role=self.role,
            created_by=self.user
        )

    def test_user_role_creation(self):
        self.assertEqual(self.user_role.user, self.user)
        self.assertEqual(self.user_role.role, self.role)
        self.assertEqual(self.user_role.created_by, self.user)

    def test_user_role_str(self):
        expected = f"{self.user} - {self.role}"
        self.assertEqual(str(self.user_role), expected)

    def test_user_role_validation(self):
        with self.assertRaises(ValidationError):
            UserRole.objects.create(user=None, role=None, created_by=self.user)
