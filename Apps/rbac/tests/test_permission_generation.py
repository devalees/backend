from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from ..models import RBACPermission, FieldPermission, TestDocument
from ..permissions.generation import generate_permissions

User = get_user_model()

class AutomaticPermissionGenerationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'
        )
        self.content_type = ContentType.objects.get_for_model(TestDocument)
        self.permissions = RBACPermission.objects.filter(content_type=self.content_type)
        self.field_permissions = FieldPermission.objects.filter(content_type=self.content_type)
        generate_permissions(TestDocument)

    def test_model_level_permissions_created(self):
        """Test that model-level permissions are created correctly."""
        permissions = RBACPermission.objects.filter(content_type=self.content_type)
        self.assertEqual(permissions.count(), 4)  # view, add, change, delete
        codenames = set(permissions.values_list('codename', flat=True))
        self.assertEqual(codenames, {'view', 'add', 'change', 'delete'})

    def test_field_level_permissions_created(self):
        """Test that field-level permissions are created for all fields."""
        # Get all fields from the model
        model_fields = {f.name for f in TestDocument._meta.get_fields() if not f.is_relation}
        
        # Get fields that have permissions
        fields_with_permissions = {
            permission.field_name for permission in self.field_permissions
        }
        
        # Remove system fields that shouldn't have permissions
        system_fields = {'id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_active'}
        expected_fields = model_fields - system_fields
        actual_fields = fields_with_permissions - system_fields
        
        self.assertEqual(actual_fields, expected_fields)

    def test_field_permission_types_are_correct(self):
        """Test that field permissions have valid types."""
        field_permissions = FieldPermission.objects.filter(content_type=self.content_type)
        valid_types = {'read', 'write', 'delete', 'view', 'change', 'add'}
        for permission in field_permissions:
            self.assertIn(permission.permission_type, valid_types)

    def test_permission_names_are_correct(self):
        """Test that permission names are formatted correctly."""
        permissions = RBACPermission.objects.filter(content_type=self.content_type)
        for permission in permissions:
            self.assertTrue(permission.name.startswith('Can '))
            self.assertTrue(permission.name.lower().endswith('test document'))

    def test_permissions_are_unique(self):
        """Test that permissions are not duplicated."""
        field_count = len([f for f in TestDocument._meta.get_fields() if not f.is_relation])
        field_permissions = RBACPermission.objects.filter(
            content_type=self.content_type,
            field_name__isnull=False
        ).count()
        # Each field should have read, write, and delete permissions
        self.assertEqual(field_permissions, field_count * 3) 