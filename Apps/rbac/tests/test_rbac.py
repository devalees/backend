from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from ..models import Role, RBACPermission, FieldPermission, RolePermission, UserRole, TestDocument
from ..factories import UserFactory

User = get_user_model()

class RBACModelTest(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regular123'
        )
        self.viewer_user = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='viewer123'
        )
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='editor123'
        )

        # Create test roles
        self.admin_role = Role.objects.create(
            name='admin',
            description='Administrator role',
            created_by=self.admin_user
        )
        self.editor_role = Role.objects.create(
            name='editor',
            description='Editor role',
            created_by=self.admin_user
        )
        self.viewer_role = Role.objects.create(
            name='viewer',
            description='Viewer role',
            created_by=self.admin_user
        )

        # Get content type for TestDocument
        self.content_type = ContentType.objects.get_for_model(TestDocument)

        # Create permissions
        self.view_permission = RBACPermission.objects.create(
            name='View TestDocument',
            codename='view_testdocument',
            content_type=self.content_type,
            created_by=self.admin_user
        )
        self.change_permission = RBACPermission.objects.create(
            name='Change TestDocument',
            codename='change_testdocument',
            content_type=self.content_type,
            created_by=self.admin_user
        )
        self.delete_permission = RBACPermission.objects.create(
            name='Delete TestDocument',
            codename='delete_testdocument',
            content_type=self.content_type,
            created_by=self.admin_user
        )

        # Create field permissions
        self.title_field_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='title',
            permission_type='view',
            defaults={'created_by': self.admin_user}
        )
        self.content_field_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='content',
            permission_type='view',
            defaults={'created_by': self.admin_user}
        )
        self.secret_key_field_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='secret_key',
            permission_type='view',
            defaults={'created_by': self.admin_user}
        )

        # Create additional field permissions for change
        self.title_change_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='title',
            permission_type='change',
            defaults={'created_by': self.admin_user}
        )
        self.content_change_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='content',
            permission_type='change',
            defaults={'created_by': self.admin_user}
        )
        self.secret_key_change_permission, _ = FieldPermission.objects.get_or_create(
            content_type=self.content_type,
            field_name='secret_key',
            permission_type='change',
            defaults={'created_by': self.admin_user}
        )

        # Assign permissions to roles
        RolePermission.objects.create(
            role=self.admin_role,
            permission=self.view_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.admin_role,
            permission=self.change_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.admin_role,
            permission=self.delete_permission,
            created_by=self.admin_user
        )

        # Assign permissions to editor role
        RolePermission.objects.create(
            role=self.editor_role,
            permission=self.view_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.editor_role,
            permission=self.change_permission,
            created_by=self.admin_user
        )

        # Assign permissions to viewer role
        RolePermission.objects.create(
            role=self.viewer_role,
            permission=self.view_permission,
            created_by=self.admin_user
        )

        # Assign field permissions to editor role
        RolePermission.objects.create(
            role=self.editor_role,
            field_permission=self.title_field_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.editor_role,
            field_permission=self.content_field_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.editor_role,
            field_permission=self.title_change_permission,
            created_by=self.admin_user
        )
        RolePermission.objects.create(
            role=self.editor_role,
            field_permission=self.content_change_permission,
            created_by=self.admin_user
        )

        # Assign field permissions to viewer role
        RolePermission.objects.create(
            role=self.viewer_role,
            field_permission=self.content_field_permission,
            created_by=self.admin_user
        )

        # Assign roles to users
        UserRole.objects.create(
            user=self.regular_user,
            role=self.editor_role,
            created_by=self.admin_user
        )
        UserRole.objects.create(
            user=self.editor_user,
            role=self.editor_role,
            created_by=self.admin_user
        )
        UserRole.objects.create(
            user=self.viewer_user,
            role=self.viewer_role,
            created_by=self.admin_user
        )

        # Create test document
        self.user = UserFactory()
        self.test_doc = TestDocument(
            title='Test Document',
            content='Test Content',
            secret_key='test123',
            user=self.user,
            created_by=self.user
        )
        self.test_doc.save(user=self.user)

    def test_model_level_permissions(self):
        """Test model-level permission checks"""
        # Admin should have all permissions
        self.assertTrue(self.test_doc.can_view(self.admin_user))
        self.assertTrue(self.test_doc.can_change(self.admin_user))
        self.assertTrue(self.test_doc.can_delete(self.admin_user))

        # Editor should have view and edit permissions
        self.assertTrue(self.test_doc.can_view(self.regular_user))
        self.assertTrue(self.test_doc.can_change(self.regular_user))
        self.assertFalse(self.test_doc.can_delete(self.regular_user))

        # Viewer should only have view permission
        self.assertTrue(self.test_doc.can_view(self.viewer_user))
        self.assertFalse(self.test_doc.can_change(self.viewer_user))
        self.assertFalse(self.test_doc.can_delete(self.viewer_user))

    def test_field_level_permissions(self):
        """Test field-level permission checks"""
        # Admin should have access to all fields
        admin_fields = self.test_doc.get_accessible_fields(self.admin_user)
        self.assertIn('title', admin_fields)
        self.assertIn('content', admin_fields)
        self.assertIn('secret_key', admin_fields)

        # Editor should have access to title and content
        editor_fields = self.test_doc.get_accessible_fields(self.editor_user)
        self.assertIn('title', editor_fields)
        self.assertIn('content', editor_fields)
        self.assertNotIn('secret_key', editor_fields)

        # Viewer should only have access to content
        viewer_fields = self.test_doc.get_accessible_fields(self.viewer_user)
        self.assertNotIn('title', viewer_fields)
        self.assertIn('content', viewer_fields)
        self.assertNotIn('secret_key', viewer_fields)

    def test_permission_denied(self):
        """Test that permission denied is raised when appropriate"""
        # Viewer should not be able to edit
        with self.assertRaises(PermissionDenied):
            self.test_doc.check_permission(self.viewer_user, 'change')

        # Editor should not be able to delete
        with self.assertRaises(PermissionDenied):
            self.test_doc.check_permission(self.regular_user, 'delete')

    def test_queryset_filtering(self):
        """Test that queryset filtering works correctly"""
        # Create additional test documents
        TestDocument.objects.create(
            title='Admin Document',
            content='Admin Content',
            created_by=self.admin_user,
            user=self.admin_user
        )
        TestDocument.objects.create(
            title='Editor Document',
            content='Editor Content',
            created_by=self.regular_user,
            user=self.regular_user
        )

        # Admin should see all documents
        admin_docs = TestDocument.get_queryset_for_user(self.admin_user)
        self.assertEqual(admin_docs.count(), 3)

        # Editor should see all documents
        editor_docs = TestDocument.get_queryset_for_user(self.editor_user)
        self.assertEqual(editor_docs.count(), 3)

        # Viewer should see all documents
        viewer_docs = TestDocument.get_queryset_for_user(self.viewer_user)
        self.assertEqual(viewer_docs.count(), 3)

    def test_user_tracking(self):
        """Test that user tracking works correctly"""
        # Test that created_by and updated_by are set correctly
        self.assertEqual(self.test_doc.created_by, self.user)
        self.assertEqual(self.test_doc.updated_by, self.user)

        # Test that updated_by is updated when saving
        self.test_doc.title = 'Updated Title'
        self.test_doc.save(user=self.admin_user)
        self.assertEqual(self.test_doc.updated_by, self.admin_user)

    def test_field_permission_validation(self):
        """Test field permission validation"""
        # Test invalid field name
        with self.assertRaises(ValidationError):
            FieldPermission.objects.create(
                content_type=self.content_type,
                field_name='nonexistent_field',
                permission_type='view',
                created_by=self.admin_user
            )

    def test_role_permission_validation(self):
        """Test role permission validation"""
        # Test that role permission validation works correctly
        role_permission = RolePermission(
            role=self.admin_role,
            field_permission=self.title_field_permission,
            created_by=self.admin_user
        )
        role_permission.full_clean()
        role_permission.save()

        # Test that duplicate role permissions are not allowed
        with self.assertRaises(ValidationError):
            role_permission = RolePermission(
                role=self.admin_role,
                field_permission=self.title_field_permission,
                created_by=self.admin_user
            )
            role_permission.full_clean()

        # Test that both permission and field_permission cannot be set
        with self.assertRaises(ValidationError):
            role_permission = RolePermission(
                role=self.admin_role,
                permission=self.view_permission,
                field_permission=self.title_field_permission,
                created_by=self.admin_user
            )
            role_permission.full_clean()

        # Test that either permission or field_permission must be set
        with self.assertRaises(ValidationError):
            role_permission = RolePermission(
                role=self.admin_role,
                created_by=self.admin_user
            )
            role_permission.full_clean()