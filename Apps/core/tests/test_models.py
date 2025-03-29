import pytest
from django.test import TestCase
from django.db import models, connection, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.core.models import BaseModel
from Apps.core.tests.factories import UserFactory, BaseModelFactory
from datetime import timedelta

User = get_user_model()

class TestModel(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'test_model'

class TestBaseModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()

    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set when object is created"""
        with transaction.atomic():
            connection.disable_constraint_checking()
            try:
                obj = TestModel.objects.create(name="Test Object", created_by=self.user, updated_by=self.user)
                assert obj.created_at is not None
            finally:
                connection.enable_constraint_checking()

    def test_updated_at_auto_now(self):
        """Test that updated_at is automatically updated when object is modified"""
        with transaction.atomic():
            connection.disable_constraint_checking()
            try:
                obj = TestModel.objects.create(name="Test Object", created_by=self.user, updated_by=self.user)
                initial_updated_at = obj.updated_at
                obj.save()
                assert obj.updated_at > initial_updated_at
            finally:
                connection.enable_constraint_checking()

    def test_created_by_auto_set(self):
        """Test that created_by is automatically set when object is created"""
        obj = TestModel.objects.create(name="Test Object", created_by=self.user)
        assert obj.created_by == self.user

    def test_updated_by_auto_set(self):
        """Test that updated_by is automatically set when object is modified"""
        obj = TestModel.objects.create(name="Test Object", created_by=self.user)
        obj.name = "Updated Name"
        obj.updated_by = self.user
        obj.save()
        assert obj.updated_by == self.user

@pytest.mark.django_db
class TestUser:
    def test_create_user(self):
        """Test creating a regular user"""
        user = UserFactory()
        assert user.username is not None
        assert user.email is not None
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = UserFactory(is_superuser=True, is_staff=True)
        assert admin_user.username is not None
        assert admin_user.email is not None
        assert admin_user.check_password('testpass123')
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_user_str(self):
        """Test the string representation of the user"""
        user = UserFactory()
        assert str(user) == user.username

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
        user = UserFactory()
        assert not user.is_staff
        assert not user.is_superuser

        user.is_staff = True
        user.save()
        assert user.is_staff

        user.is_superuser = True
        user.save()
        assert user.is_superuser 