from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError
from ..models import Role, RBACPermission, FieldPermission, RolePermission, UserRole, TestDocument
from ..serializers import (
    RoleSerializer,
    RBACPermissionSerializer,
    FieldPermissionSerializer,
    RolePermissionSerializer,
    UserRoleSerializer
)
from unittest.mock import Mock

User = get_user_model()

class RBACPermissionSerializerTests(TestCase):
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

    def test_permission_serializer(self):
        """Test permission serializer."""
        serializer = RBACPermissionSerializer(self.permission)
        data = serializer.data
        self.assertEqual(data['content_type'], self.content_type.id)
        self.assertEqual(data['codename'], 'test_permission')
        self.assertEqual(data['name'], 'Test Permission')

class FieldPermissionSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission_data = {
            'content_type': self.content_type,
            'field_name': 'username',
            'permission_type': 'view',
            'created_by': self.user,
            'updated_by': self.user
        }
        self.field_permission = FieldPermission.objects.create(**self.field_permission_data)

    def test_field_permission_serializer(self):
        serializer = FieldPermissionSerializer(self.field_permission)
        data = serializer.data
        self.assertEqual(data['content_type']['id'], self.content_type.id)
        self.assertEqual(data['field_name'], self.field_permission_data['field_name'])
        self.assertEqual(data['permission_type'], self.field_permission_data['permission_type'])

    def test_field_permission_serializer_validation(self):
        invalid_data = {
            'content_type': {'app_label': 'auth', 'model': 'user'},  # Invalid content type format
            'field_name': 'invalid_field',
            'permission_type': 'invalid'
        }
        serializer = FieldPermissionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

class RoleSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(name='Test Role', created_by=self.user)
        self.permission = RBACPermission.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            codename='test_permission',
            name='Test Permission',
            created_by=self.user
        )
        self.role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )

    def test_role_serializer(self):
        serializer = RoleSerializer(self.role)
        data = serializer.data
        self.assertEqual(data['name'], self.role.name)
        self.assertIn('role_permissions', data)
        self.assertEqual(len(data['role_permissions']), 1)
        self.assertEqual(data['role_permissions'][0]['permission']['codename'], self.permission.codename)

    def test_role_serializer_create(self):
        """Test role serializer create method."""
        data = {
            'name': 'New Test Role',
            'description': 'Test Description',
            'created_by': self.user.id,
            'updated_by': self.user.id
        }
        serializer = RoleSerializer(data=data, context={'request': Mock(user=self.user)})
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())
        role = serializer.save()
        self.assertEqual(role.name, data['name'])
        self.assertEqual(role.description, data['description'])
        self.assertEqual(role.role_permissions.count(), 0)  # No permissions should be created by default
        self.assertEqual(role.created_by, self.user)
        self.assertEqual(role.updated_by, self.user)

    def test_role_serializer_update(self):
        """Test role serializer update method."""
        new_permission = RBACPermission.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            codename='new_permission',
            name='New Permission',
            created_by=self.user
        )
        data = {
            'name': 'Updated Role',
            'description': 'Updated Description'
        }
        serializer = RoleSerializer(self.role, data=data, context={'request': Mock(user=self.user)})
        self.assertTrue(serializer.is_valid())
        updated_role = serializer.save()
        self.assertEqual(updated_role.name, 'Updated Role')
        self.assertEqual(updated_role.role_permissions.count(), 1)

class RolePermissionSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.user,
            updated_by=self.user
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = RBACPermission.objects.create(
            name='Test Permission',
            codename='test_permission',
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )

    def test_role_permission_serializer(self):
        serializer = RolePermissionSerializer(self.role_permission)
        data = serializer.data
        self.assertEqual(data['role'], self.role.id)
        self.assertEqual(data['permission']['id'], self.permission.id)

class UserRoleSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.user,
            updated_by=self.user
        )
        self.user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.user
        )

    def test_user_role_serializer(self):
        serializer = UserRoleSerializer(self.user_role)
        data = serializer.data
        self.assertEqual(data['user'], self.user.id)
        self.assertEqual(data['role']['id'], self.role.id)
        self.assertEqual(data['role']['name'], self.role.name)

    def test_user_role_serializer_validation(self):
        # Test unique constraint validation
        data = {
            'user': self.user.id,
            'role': self.role.id
        }
        serializer = UserRoleSerializer(data=data)
        self.assertFalse(serializer.is_valid()) 