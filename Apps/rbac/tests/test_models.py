from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from ..models import Role, Permission, FieldPermission, RolePermission, UserRole

User = get_user_model()

class RoleTests(TestCase):
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

    def test_create_role(self):
        role = Role.objects.create(**self.role_data)
        self.assertEqual(role.name, 'Test Role')
        self.assertEqual(role.description, 'Test Description')

    def test_role_str(self):
        role = Role.objects.create(**self.role_data)
        self.assertEqual(str(role), 'Test Role')

    def test_role_validation(self):
        with self.assertRaises(ValidationError):
            role = Role(name='')
            role.clean()

class PermissionTests(TestCase):
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

    def test_create_permission(self):
        permission = Permission.objects.create(**self.permission_data)
        self.assertEqual(permission.name, 'Test Permission')
        self.assertEqual(permission.codename, 'test_permission')
        self.assertEqual(permission.content_type, self.content_type)

    def test_permission_str(self):
        permission = Permission.objects.create(**self.permission_data)
        self.assertEqual(str(permission), 'Test Permission (test_permission)')

    def test_permission_validation(self):
        with self.assertRaises(ValidationError):
            permission = Permission(name='', codename='')
            permission.clean()

class FieldPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission_data = {
            'content_type': self.content_type,
            'field_name': 'test_field',
            'permission_type': 'view',
            'created_by': self.user,
            'updated_by': self.user
        }

    def test_create_field_permission(self):
        field_permission = FieldPermission.objects.create(**self.field_permission_data)
        self.assertEqual(field_permission.field_name, 'test_field')
        self.assertEqual(field_permission.permission_type, 'view')

    def test_field_permission_str(self):
        field_permission = FieldPermission.objects.create(**self.field_permission_data)
        self.assertEqual(str(field_permission), 'test_field - View')

    def test_field_permission_validation(self):
        with self.assertRaises(ValidationError):
            field_permission = FieldPermission(
                content_type=self.content_type,
                field_name='nonexistent_field',
                permission_type='view',
                created_by=self.user
            )
            field_permission.clean()

class RolePermissionTests(TestCase):
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
            codename='view',
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='test_field',
            permission_type='view',
            created_by=self.user,
            updated_by=self.user
        )

    def test_create_role_permission(self):
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )
        self.assertEqual(role_permission.role, self.role)
        self.assertEqual(role_permission.permission, self.permission)

    def test_create_role_field_permission(self):
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            field_permission=self.field_permission,
            created_by=self.user
        )
        self.assertEqual(role_permission.role, self.role)
        self.assertEqual(role_permission.field_permission, self.field_permission)

    def test_role_permission_str(self):
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user
        )
        self.assertEqual(str(role_permission), 'Test Role - view')

    def test_role_permission_validation(self):
        with self.assertRaises(ValidationError):
            role_permission = RolePermission(
                role=self.role,
                permission=Permission.objects.create(
                    name='Different Permission',
                    codename='add',
                    content_type=self.content_type,
                    created_by=self.user,
                    updated_by=self.user
                ),
                field_permission=self.field_permission,
                created_by=self.user
            )
            role_permission.clean()

class UserRoleTests(TestCase):
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
        self.user_role_data = {
            'user': self.user,
            'role': self.role,
            'created_by': self.user
        }

    def test_create_user_role(self):
        user_role = UserRole.objects.create(**self.user_role_data)
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)

    def test_user_role_str(self):
        user_role = UserRole.objects.create(**self.user_role_data)
        self.assertEqual(str(user_role), 'testuser - Test Role')

    def test_user_role_unique_constraint(self):
        UserRole.objects.create(**self.user_role_data)
        with self.assertRaises(ValidationError):
            user_role = UserRole(**self.user_role_data)
            user_role.clean()
