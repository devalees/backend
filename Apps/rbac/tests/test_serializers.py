from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import Permission, FieldPermission, Role, RolePermission, UserRole
from ..serializers import (
    PermissionSerializer,
    FieldPermissionSerializer,
    RoleSerializer,
    RolePermissionSerializer,
    UserRoleSerializer,
)

User = get_user_model()

class PermissionSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission_data = {
            'name': 'Test Permission',
            'codename': 'test_permission',
            'content_type': self.content_type,
            'created_by': self.user,
            'updated_by': self.user
        }
        self.permission = Permission.objects.create(**self.permission_data)

    def test_permission_serializer(self):
        serializer = PermissionSerializer(self.permission)
        data = serializer.data
        self.assertEqual(data['name'], self.permission_data['name'])
        self.assertEqual(data['codename'], self.permission_data['codename'])
        self.assertEqual(data['content_type']['id'], self.content_type.id)

class FieldPermissionSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission_data = {
            'content_type': self.content_type,
            'field_name': 'username',
            'permission_type': 'view',
            'description': 'Test Description',
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
        self.assertEqual(data['description'], self.field_permission_data['description'])

    def test_field_permission_serializer_validation(self):
        invalid_data = {
            'content_type': {'app_label': 'auth', 'model': 'user'},  # Invalid content type format
            'field_name': 'invalid_field',
            'permission_type': 'invalid',
            'description': 'Test'
        }
        serializer = FieldPermissionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

class RoleSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.role_data = {
            'name': 'Test Role',
            'description': 'Test Description',
            'created_by': self.user,
            'updated_by': self.user
        }
        self.role = Role.objects.create(**self.role_data)
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='test_permission',
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
            created_by=self.user,
            updated_by=self.user
        )

    def test_role_serializer(self):
        RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )
        serializer = RoleSerializer(self.role)
        data = serializer.data
        self.assertEqual(data['name'], self.role_data['name'])
        self.assertEqual(data['description'], self.role_data['description'])
        self.assertIn('permissions', data)
        self.assertIn('field_permissions', data)

    def test_role_serializer_create(self):
        # Create a permission for the field permission
        field_permission_permission = Permission.objects.create(
            name='View Field Permission',
            codename='view',
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        
        data = {
            'name': 'New Role',
            'description': 'New Description',
            'permission_ids': [self.permission.id],
            'field_permission_ids': [self.field_permission.id]
        }
        serializer = RoleSerializer(data=data, context={'request': type('Request', (), {'user': self.user})})
        self.assertTrue(serializer.is_valid())
        role = serializer.save()
        self.assertEqual(role.name, data['name'])
        self.assertEqual(role.description, data['description'])
        self.assertEqual(role.role_permissions.count(), 2)

    def test_role_serializer_update(self):
        data = {
            'name': 'Updated Role',
            'description': 'Updated Description',
            'permission_ids': [self.permission.id]
        }
        serializer = RoleSerializer(
            self.role,
            data=data,
            context={'request': type('Request', (), {'user': self.user})}
        )
        self.assertTrue(serializer.is_valid())
        updated_role = serializer.save()
        self.assertEqual(updated_role.name, data['name'])
        self.assertEqual(updated_role.description, data['description'])
        self.assertEqual(updated_role.role_permissions.count(), 1)

class RolePermissionSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.user,
            updated_by=self.user
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
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
        self.assertEqual(data['permission'], self.permission.id)

class UserRoleSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
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
            'role_id': self.role.id
        }
        serializer = UserRoleSerializer(data=data)
        self.assertFalse(serializer.is_valid()) 