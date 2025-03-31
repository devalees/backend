import pytest
from django.test import TestCase
from django.db import models, connection, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.core.models import BaseModel
from Apps.core.tests.factories import UserFactory, BaseModelFactory
import time

User = get_user_model()

class TestModel(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'test_model'

    def __str__(self):
        return self.name

class TestBaseModel(TestCase):
    """Test cases for BaseModel."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_created_at_auto_now_add(self):
        """Test created_at is set automatically on creation."""
        model = TestModel.objects.create(name='Test')
        self.assertIsNotNone(model.created_at)
        self.assertTrue(timezone.is_aware(model.created_at))

    def test_updated_at_auto_now(self):
        """Test updated_at is updated automatically."""
        model = TestModel.objects.create(name='Test')
        original_updated_at = model.updated_at
        time.sleep(0.1)  # Ensure time difference
        model.name = 'Updated'
        model.save()
        self.assertGreater(model.updated_at, original_updated_at)

    def test_created_by_updated_by(self):
        """Test created_by and updated_by fields."""
        model = TestModel.objects.create(name='Test', created_by=self.user, updated_by=self.user)
        self.assertEqual(model.created_by, self.user)
        self.assertEqual(model.updated_by, self.user)

        new_user = UserFactory()
        model.updated_by = new_user
        model.save()
        assert model.updated_by == new_user

    def test_is_active_default(self):
        """Test is_active default value."""
        model = TestModel.objects.create(name='Test')
        self.assertTrue(model.is_active)

    def test_soft_delete(self):
        """Test soft delete functionality."""
        model = TestModel.objects.create(name='Test')
        model.is_active = False
        model.save()
        self.assertFalse(model.is_active)
        self.assertFalse(TestModel.objects.filter(pk=model.pk).exists())
        self.assertTrue(TestModel.all_objects.filter(pk=model.pk).exists())

    def test_str_representation(self):
        """Test string representation."""
        model = TestModel.objects.create(name='Test')
        self.assertEqual(str(model), 'Test')

@pytest.mark.django_db
class TestUser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = UserFactory()
        self.superuser = UserFactory(is_superuser=True, is_staff=True)

    def test_create_user(self):
        """Test creating a new user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Test creating a superuser"""
        assert self.superuser.username is not None
        assert self.superuser.email is not None
        assert self.superuser.check_password('testpass123')
        assert self.superuser.is_staff
        assert self.superuser.is_superuser

    def test_user_str(self):
        """Test the string representation of the user"""
        assert str(self.user) == self.user.username

    def test_user_email_normalized(self):
        """Test that email is normalized when creating a user"""
        email = 'test@EXAMPLE.com'
        user = UserFactory(email=email)
        assert user.email == email.lower()

    def test_invalid_email(self):
        """Test creating user with no email raises error"""
        with pytest.raises(ValueError):
            UserFactory(email=None)

    def test_create_user_without_password(self):
        """Test creating user without password"""
        user = UserFactory(password=None)
        assert user.check_password('') is False

    def test_user_permissions(self):
        """Test user permissions"""
        assert not self.user.is_staff
        assert not self.user.is_superuser

        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff

        self.user.is_superuser = True
        self.user.save()
        assert self.user.is_superuser 