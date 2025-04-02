from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse, get_resolver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient
from ..models import RBACPermission, FieldPermission, Role, RolePermission, UserRole, TestDocument
from .factories import UserFactory, RoleFactory, PermissionFactory, FieldPermissionFactory, RolePermissionFactory, UserRoleFactory

User = get_user_model()

class PermissionViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.force_authenticate(user=self.admin)
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = RBACPermission.objects.create(
            content_type=self.content_type,
            codename='test_permission',
            name='Test Permission',
            created_by=self.admin
        )

    def test_list_permissions(self):
        """Test listing permissions."""
        response = self.client.get(reverse('rbac:permission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_permission(self):
        """Test creating a permission."""
        data = {
            'content_type': self.content_type.id,
            'codename': 'new_permission',
            'name': 'New Permission',
            'created_by': self.admin.id,
            'updated_by': self.admin.id
        }
        response = self.client.post(reverse('rbac:permission-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RBACPermission.objects.filter(created_by=self.admin).count(), 2)

    def test_create_permission_non_admin(self):
        """Test creating a permission as non-admin."""
        self.client.force_authenticate(user=self.user)
        data = {
            'content_type': self.content_type.id,
            'codename': 'new_permission',
            'name': 'New Permission',
            'created_by': self.user.id
        }
        response = self.client.post(reverse('rbac:permission-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_permissions_unauthorized(self):
        """Test listing permissions without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('rbac:permission-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class FieldPermissionViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.client.force_authenticate(user=self.admin)
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
            created_by=self.admin
        )

    def test_list_field_permissions(self):
        """Test listing field permissions."""
        response = self.client.get(reverse('rbac:fieldpermission-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_field_permission(self):
        """Test creating a field permission."""
        data = {
            'content_type': self.content_type.id,
            'field_name': 'email',
            'permission_type': 'view',
            'created_by': self.admin.id,
            'updated_by': self.admin.id
        }
        response = self.client.post(reverse('rbac:fieldpermission-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FieldPermission.objects.filter(created_by=self.admin).count(), 2)

    def test_available_fields(self):
        """Test getting available fields."""
        response = self.client.get(reverse('rbac:available-fields'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_fields = next((item['fields'] for item in response.data if item['model'] == 'user'), [])
        self.assertIn('username', user_fields)

class RoleViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.role = RoleFactory(created_by=self.admin, updated_by=self.admin)
        # Assign the role to the regular user
        self.user_role = UserRoleFactory(
            user=self.user,
            role=self.role,
            created_by=self.admin,
            updated_by=self.admin
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = PermissionFactory(
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )
        self.field_permission = FieldPermissionFactory(
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_roles(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:role-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_role_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:role-list')
        data = {
            'name': 'New Role',
            'description': 'New Description',
            'permissions': [self.permission.id],
            'field_permissions': [self.field_permission.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_assign_permissions(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:role-assign-permissions', args=[self.role.id])
        data = {
            'permissions': [self.permission.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        role = Role.objects.get(id=self.role.id)
        self.assertEqual(role.role_permissions.count(), 1)

class RolePermissionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.role = RoleFactory(created_by=self.admin, updated_by=self.admin)
        # Assign the role to the regular user
        self.user_role = UserRoleFactory(
            user=self.user,
            role=self.role,
            created_by=self.admin,
            updated_by=self.admin
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = PermissionFactory(
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )
        self.role_permission = RolePermissionFactory(
            role=self.role,
            permission=self.permission,
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_role_permissions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:rolepermission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_role_permission_admin(self):
        """Test creating a role permission as admin."""
        self.client.force_authenticate(user=self.admin)
        data = {
            'role': self.role.id,
            'permission': self.permission.id,
            'created_by': self.admin.id,
            'updated_by': self.admin.id
        }
        response = self.client.post(reverse('rbac:rolepermission-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RolePermission.objects.filter(created_by=self.admin).count(), 2)

class UserRoleViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.role = RoleFactory(created_by=self.admin, updated_by=self.admin)
        self.user_role = UserRoleFactory(
            user=self.user,
            role=self.role,
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_user_roles(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:userrole-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_user_role_admin(self):
        """Test creating a user role as admin."""
        self.client.force_authenticate(user=self.admin)
        data = {
            'user': self.user.id,
            'role': self.role.id,
            'created_by': self.admin.id,
            'updated_by': self.admin.id
        }
        response = self.client.post(reverse('rbac:userrole-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserRole.objects.filter(created_by=self.admin).count(), 2)

    def test_my_roles(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:userrole-my-roles')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_field_permissions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:userrole-my-field-permissions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
