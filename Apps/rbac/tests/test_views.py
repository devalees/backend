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

class PermissionViewSetTests(TestCase):
    """Test cases for RBACPermission views."""
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Delete any existing permissions and users
        RBACPermission.objects.all().delete()
        User.objects.all().delete()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = PermissionFactory(created_by=self.admin, updated_by=self.admin)

    def tearDown(self):
        """Clean up after each test."""
        RBACPermission.objects.all().delete()
        User.objects.all().delete()

    def test_list_permissions(self):
        """Test listing permissions."""
        # Delete any existing permissions except the one created in setUp
        RBACPermission.objects.exclude(id=self.permission.id).delete()
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:permission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['codename'], self.permission.codename)
        self.assertEqual(response.data[0]['name'], self.permission.name)

    def test_list_permissions_unauthorized(self):
        """Test listing permissions without authentication."""
        url = reverse('rbac:permission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_permission(self):
        """Test creating a permission."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:permission-list')
        data = {
            'name': 'Test Permission',
            'codename': 'test_permission',
            'content_type': self.content_type.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RBACPermission.objects.filter(created_by=self.admin).count(), 2)

    def test_create_permission_non_admin(self):
        """Test creating a permission as non-admin."""
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:permission-list')
        data = {
            'name': 'Test Permission',
            'codename': 'test_permission',
            'content_type': self.content_type.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class FieldPermissionViewSetTests(TestCase):
    """Test cases for FieldPermission views."""
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Delete any existing field permissions and users
        FieldPermission.objects.all().delete()
        User.objects.all().delete()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission = FieldPermissionFactory(
            content_type=self.content_type,
            field_name='email',
            permission_type='read',
            created_by=self.admin,
            updated_by=self.admin
        )

    def tearDown(self):
        """Clean up after each test."""
        FieldPermission.objects.all().delete()
        User.objects.all().delete()

    def test_list_field_permissions(self):
        """Test listing field permissions."""
        # Delete any existing field permissions except the one created in setUp
        FieldPermission.objects.exclude(id=self.field_permission.id).delete()
        url = reverse('rbac:fieldpermission-list')
        self.client.force_authenticate(user=self.admin)  # Authenticate as admin
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['field_name'], 'email')

    def test_create_field_permission(self):
        """Test creating a field permission."""
        self.client.force_authenticate(user=self.admin)
        content_type = ContentType.objects.get_for_model(User)
        data = {
            'content_type': content_type.id,
            'field_name': 'username',
            'permission_type': 'read'
        }
        response = self.client.post('/api/v1/rbac/field-permissions/', data)
        print("Response content:", response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FieldPermission.objects.count(), 2)
        field_permission = FieldPermission.objects.last()
        self.assertEqual(field_permission.field_name, 'username')
        self.assertEqual(field_permission.permission_type, 'read')
        self.assertEqual(field_permission.created_by, self.admin)
        self.assertEqual(field_permission.updated_by, self.admin)

    def test_available_fields(self):
        """Test getting available fields."""
        self.client.force_authenticate(user=self.admin)  # Authenticate as admin
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
        """Test assigning permissions to a role."""
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:role-assign-permissions', args=[self.role.id])
        data = {
            'permissions': [self.permission.id]
        }
        # Clear existing permissions first
        RolePermission.objects.filter(role=self.role).delete()
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        role = Role.objects.get(id=self.role.id)
        self.assertEqual(role.role_permissions.filter(permission__isnull=False).count(), 1)

class RolePermissionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.role = RoleFactory(created_by=self.admin, updated_by=self.admin)
        self.role2 = RoleFactory(created_by=self.admin, updated_by=self.admin)  # Second role for testing
        self.permission = PermissionFactory(created_by=self.admin, updated_by=self.admin)
        self.permission2 = PermissionFactory(created_by=self.admin, updated_by=self.admin)  # Second permission for testing
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
        url = reverse('rbac:rolepermission-list')
        data = {
            'role': self.role2.id,
            'permission_id': self.permission2.id  # Using permission_id as expected by the serializer
        }
        response = self.client.post(url, data=data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Response data:", response.data)  # Print response data on failure
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RolePermission.objects.count(), 2)  # Including the one created in setUp
        role_permission = RolePermission.objects.last()
        self.assertEqual(role_permission.role, self.role2)
        self.assertEqual(role_permission.permission, self.permission2)

class UserRoleViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.user2 = UserFactory()  # Second user for testing
        self.admin = UserFactory(is_superuser=True, is_staff=True)
        self.role = RoleFactory(created_by=self.admin, updated_by=self.admin)
        self.role2 = RoleFactory(created_by=self.admin, updated_by=self.admin)  # Second role for testing
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
        url = reverse('rbac:userrole-list')
        data = {
            'user_id': self.user2.id,  # Changed from user to user_id
            'role_id': self.role2.id   # Changed from role to role_id
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserRole.objects.count(), 2)  # Including the one created in setUp
        user_role = UserRole.objects.last()
        self.assertEqual(user_role.user, self.user2)
        self.assertEqual(user_role.role, self.role2)

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
