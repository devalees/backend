import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import models, connection
from django.db.migrations.executor import MigrationExecutor
from ..models import RBACBaseModel
from Apps.entity.models import Organization

User = get_user_model()

class TestRBACBaseModel(TransactionTestCase):
    """Test suite for RBACBaseModel functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        super().setUpClass()
        
        # Create test model
        class TestModel(RBACBaseModel):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'rbac'
        
        cls.test_model = TestModel
        
        # Create the table for TestModel
        connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(TestModel)
        finally:
            connection.enable_constraint_checking()

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username=f'testuser_{self._testMethodName}',  # Make username unique per test
            email=f'test_{self._testMethodName}@example.com',  # Make email unique per test
            password='testpass123'
        )
        
        # Create a test organization
        self.organization = Organization.objects.create(
            name=f'Test Organization {self._testMethodName}',  # Make name unique per test
            description='Test Organization Description'
        )
        
        self.test_instance = self.test_model.objects.create(
            name='Test Instance',
            organization=self.organization
        )

    def tearDown(self):
        """Clean up after each test"""
        # Delete test data in reverse order to avoid foreign key constraints
        if hasattr(self, 'test_instance'):
            self.test_model.objects.all().delete()
        if hasattr(self, 'organization'):
            self.organization.delete()
        if hasattr(self, 'user'):
            self.user.delete()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        connection.disable_constraint_checking()
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(cls.test_model)
        finally:
            connection.enable_constraint_checking()
                
        super().tearDownClass()

    def test_field_permission_default(self):
        """Test that field permissions default to True"""
        field_name = 'name'
        self.assertTrue(self.test_instance.get_field_permission(self.user, field_name))

    def test_organization_isolation(self):
        """Test that organization field is properly set up"""
        self.assertEqual(self.test_instance.organization_id, self.organization.id)
        self.assertTrue(hasattr(self.test_instance, 'organization'))

    def test_timestamp_fields(self):
        """Test that timestamp fields are automatically updated"""
        self.assertIsNotNone(self.test_instance.created_at)
        self.assertIsNotNone(self.test_instance.updated_at)

    def test_model_abstract(self):
        """Test that RBACBaseModel is abstract"""
        self.assertTrue(RBACBaseModel._meta.abstract)

    def test_related_name_generation(self):
        """Test that related_name is properly generated for organization field"""
        field = self.test_instance._meta.get_field('organization')
        self.assertEqual(field.remote_field.related_name, 'testmodel_related') 