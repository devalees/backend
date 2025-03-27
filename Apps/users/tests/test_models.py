import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        """Test creating a new user with username"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Test creating a new superuser with username"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin_user.username == 'admin'
        assert admin_user.email == 'admin@example.com'
        assert admin_user.is_active
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_create_user_without_username(self):
        """Test creating a user without username raises error"""
        with pytest.raises(ValueError):
            User.objects.create_user(None, 'test@example.com', 'testpass123')

    def test_create_user_without_email(self):
        """Test creating a user without email raises error"""
        with pytest.raises(ValueError):
            User.objects.create_user('testuser', None, 'testpass123')

    def test_create_user_without_password(self):
        """Test creating a user without password"""
        user = User.objects.create_user('testuser', 'test@example.com')
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('')  # Empty password

    def test_create_superuser_without_username(self):
        """Test creating a superuser without username raises error"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(None, 'admin@example.com', 'adminpass123')

    def test_create_superuser_without_email(self):
        """Test creating a superuser without email raises error"""
        with pytest.raises(ValueError):
            User.objects.create_superuser('admin', None, 'adminpass123')

    def test_create_superuser_with_is_staff_false(self):
        """Test creating a superuser with is_staff=False raises error"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )

    def test_create_superuser_with_is_superuser_false(self):
        """Test creating a superuser with is_superuser=False raises error"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )

    def test_user_str(self):
        """Test the user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        assert str(user) == 'testuser'

    def test_user_full_name(self):
        """Test the user full name property"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        assert user.get_full_name() == 'Test User'

    def test_user_short_name(self):
        """Test the user short name property"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        assert user.get_short_name() == 'Test'

    def test_username_normalization(self):
        """Test username normalization"""
        user = User.objects.create_user(
            username='TestUser',
            email='test@example.com'
        )
        assert user.username == 'TestUser'  # Username should be case-sensitive

    def test_email_normalization(self):
        """Test email normalization"""
        user = User.objects.create_user(
            username='testuser',
            email='Test@Example.com'
        )
        # Email domain should be lowercase as per RFC 5321
        assert user.email == 'Test@example.com'  # Domain part should be lowercase 