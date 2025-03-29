from django.test import TestCase
from django.urls import reverse, get_resolver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient
from ..models import Permission, FieldPermission, Role, RolePermission, UserRole

User = get_user_model()

class PermissionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            is_staff=True
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='test_permission',
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_permissions_authorized(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:permission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_permission_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:permission-list')
        data = {
            'name': 'New Permission',
            'codename': 'new_permission',
            'content_type_input': {
                'app_label': 'users',
                'model': 'user'
            }
        }
        print("\n=== test_create_permission_admin Debug ===")
        print(f"URL: {url}")
        print(f"Data: {data}")
        print(f"Admin user: {self.admin}")
        print(f"Admin is_staff: {self.admin.is_staff}")
        print(f"Admin is_superuser: {self.admin.is_superuser}")
        print(f"Content type: {self.content_type}")
        print(f"Content type app_label: {self.content_type.app_label}")
        print(f"Content type model: {self.content_type.model}")
        print(f"Content type id: {self.content_type.id}")
        print(f"Content type exists: {ContentType.objects.filter(app_label=self.content_type.app_label, model=self.content_type.model).exists()}")
        
        # Debug URL patterns
        resolver = get_resolver()
        print("\nAll URL patterns:")
        for pattern in resolver.url_patterns:
            print(f"Pattern: {pattern.pattern}")
            if hasattr(pattern, 'url_patterns'):
                for subpattern in pattern.url_patterns:
                    print(f"  Subpattern: {subpattern.pattern}")
                    if hasattr(subpattern, 'url_patterns'):
                        for subsubpattern in subpattern.url_patterns:
                            print(f"    Subsubpattern: {subsubpattern.pattern}")
                            if hasattr(subsubpattern, 'name'):
                                print(f"      Name: {subsubpattern.name}")
                    if hasattr(subpattern, 'name'):
                        print(f"    Name: {subpattern.name}")
            if hasattr(pattern, 'name'):
                print(f"  Name: {pattern.name}")
        print("=== End Debug ===\n")
        
        response = self.client.post(url, data=data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_permission_non_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:permission-list')
        data = {
            'name': 'New Permission',
            'codename': 'new_permission',
            'content_type': self.content_type.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_permissions_unauthorized(self):
        url = reverse('rbac:permission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class FieldPermissionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            is_staff=True
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_field_permissions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:fieldpermission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_field_permission_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:fieldpermission-list')
        data = {
            'content_type_id': self.content_type.id,
            'field_name': 'email',
            'permission_type': 'view'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_available_fields(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:fieldpermission-available-fields')
        response = self.client.get(url, {'content_type_id': self.content_type.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class RoleViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            is_staff=True
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.admin,
            updated_by=self.admin
        )
        # Assign the role to the regular user
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='view',
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )
        self.field_permission = FieldPermission.objects.create(
            content_type=self.content_type,
            field_name='username',
            permission_type='view',
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
            'permission_ids': [self.permission.id],
            'field_permission_ids': [self.field_permission.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_assign_permissions(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:role-assign-permissions', args=[self.role.id])
        data = {
            'permission_ids': [self.permission.id],
            'field_permission_ids': [self.field_permission.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        role = Role.objects.get(id=self.role.id)
        self.assertEqual(role.role_permissions.count(), 2)

class RolePermissionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            is_staff=True
        )
        self.role = Role.objects.create(
            name='Test Role',
            created_by=self.admin,
            updated_by=self.admin
        )
        # Assign the role to the regular user
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = Permission.objects.create(
            name='Test Permission',
            codename='view',
            content_type=self.content_type,
            created_by=self.admin,
            updated_by=self.admin
        )

    def test_list_role_permissions(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:rolepermission-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_role_permission_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:rolepermission-list')
        data = {
            'role': self.role.id,
            'permission': self.permission.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class UserRoleViewSetTests(TestCase):
    def setUp(self):
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
        self.client = APIClient()

    def test_list_user_roles(self):
        # Assign the role specifically for this test
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:userrole-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Expecting a list of roles for the user, should contain the one we created
        self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 1) 

    def test_create_user_role_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('rbac:userrole-list')
        data = {
            'user': self.user.id,
            'role_id': self.role.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_my_roles(self):
        # Add role assignment required for the permission check
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('rbac:userrole-my-roles')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Also check that the response is a list and contains the expected role
        self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['role']['name'], self.role.name)

    def test_my_field_permissions(self):
        # Assign role if needed before the test logic
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            created_by=self.admin
        )
        self.client.force_authenticate(user=self.user)
        # Create the specific field permission we expect to find
        field_permission = FieldPermission.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            field_name='username', # Expecting this field
            permission_type='view', # Expecting this type
            created_by=self.admin,
            updated_by=self.admin
        )
        # Create a standard permission required by RolePermission
        permission = Permission.objects.create(
            name='Test View Permission',
            codename='view',
            content_type=ContentType.objects.get_for_model(User),
            created_by=self.admin,
            updated_by=self.admin
        )
        # Link the role to the field permission via RolePermission
        role_permission = RolePermission.objects.create(
            role=self.role,
            permission=permission, # Link the standard permission
            field_permission=field_permission, # Link the specific field permission
            created_by=self.admin
        )
        
        url = reverse('rbac:userrole-my-field-permissions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Updated Assertion: Check the list for the specific field permission
        found = False
        for fp_data in response.data:
            # Defensive checks for nested structure
            ct_data = fp_data.get('content_type')
            if ct_data and isinstance(ct_data, dict): 
                if (
                    fp_data.get('field_name') == 'username' and 
                    fp_data.get('permission_type') == 'view' and
                    ct_data.get('app_label') == 'users' and 
                    ct_data.get('model') == 'user'
                ):
                    found = True
                    break
            else:
                 # Optionally log or handle cases where content_type is missing or not a dict
                 print(f"Warning: Unexpected format for field permission data: {fp_data}")
                     
        self.assertTrue(found, "Expected field permission 'view username' for model 'users.user' not found in response list")
