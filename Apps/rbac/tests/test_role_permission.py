"""
Tests for the updated RolePermission model.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.transaction import atomic
from ..models import Role, RBACPermission, FieldPermission, RolePermission
from .factories import UserFactory, RoleFactory, PermissionFactory, FieldPermissionFactory

User = get_user_model()

@pytest.mark.django_db
class RolePermissionModelTest(TestCase):
    """Tests for the RolePermission model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        self.role = RoleFactory(created_by=self.user, updated_by=self.user)
        self.content_type = ContentType.objects.get_for_model(User)
        self.permission = PermissionFactory(
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.field_permission = FieldPermissionFactory(
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )
        self.role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user,
            updated_by=self.user
        )
        # Create a different permission for unique constraint testing
        self.different_permission = RBACPermission.objects.create(
            name="Different Permission",
            codename="different_permission",
            content_type=self.content_type,
            created_by=self.user,
            updated_by=self.user
        )

    def test_role_permission_creation(self):
        """Test creating a role permission."""
        self.assertEqual(self.role_permission.role, self.role)
        self.assertEqual(self.role_permission.permission, self.permission)
        self.assertIsNone(self.role_permission.field_permission)
        self.assertEqual(self.role_permission.created_by, self.user)
        self.assertEqual(self.role_permission.updated_by, self.user)
        self.assertTrue(self.role_permission.is_active)

    def test_role_permission_str(self):
        """Test string representation of role permission."""
        expected = f"{self.role} - {self.permission}"
        self.assertEqual(str(self.role_permission), expected)
        
        # Test with field permission
        role_permission_with_field = RolePermission.objects.create(
            role=self.role,
            field_permission=self.field_permission,
            created_by=self.user,
            updated_by=self.user
        )
        expected = f"{self.role} - {self.field_permission}"
        self.assertEqual(str(role_permission_with_field), expected)

    def test_role_permission_validation_no_permission_or_field(self):
        """Test validation when neither permission nor field_permission is set."""
        with self.assertRaises(ValidationError):
            RolePermission.objects.create(
                role=self.role,
                created_by=self.user,
                updated_by=self.user
            )

    def test_role_permission_validation_both_permission_and_field(self):
        """Test validation when both permission and field_permission are set."""
        with self.assertRaises(ValidationError):
            RolePermission.objects.create(
                role=self.role,
                permission=self.permission,
                field_permission=self.field_permission,
                created_by=self.user,
                updated_by=self.user
            )

    def test_role_permission_unique_constraints(self):
        """Test unique constraints for role permissions."""
        # Should raise an error for duplicate role-permission
        with atomic():
            with self.assertRaises(IntegrityError):
                RolePermission.objects.create(
                    role=self.role,
                    permission=self.permission,
                    created_by=self.user,
                    updated_by=self.user
                )
        
        # Should not raise an error for different permission
        RolePermission.objects.create(
            role=self.role,
            permission=self.different_permission,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Should not raise an error for different role
        different_role = RoleFactory(created_by=self.user, updated_by=self.user)
        RolePermission.objects.create(
            role=different_role,
            permission=self.permission,
            created_by=self.user,
            updated_by=self.user
        )

    def test_role_permission_cache_invalidation(self):
        """Test that cache is invalidated when role permission is saved or deleted."""
        # This test would require mocking the invalidate_permissions_cache function
        # For now, we'll just test that the save and delete methods don't raise errors
        self.role_permission.save()
        self.role_permission.delete()
        
        # Create a new role permission to test delete
        new_role_permission = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            created_by=self.user,
            updated_by=self.user
        )
        new_role_permission.delete() 