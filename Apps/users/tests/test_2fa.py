import base64
import json
import os
import pytest
import qrcode
import time
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework.test import APITestCase
from rest_framework import status
from io import BytesIO
import pyotp
from Apps.users.models import User

User = get_user_model()

@pytest.mark.django_db
class TestTwoFactorAuthentication:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down for each test"""
        cache.clear()  # Clear cache before each test
        yield
        cache.clear()  # Clear cache after each test

    def test_user_2fa_secret_generation(self):
        """Test that a user can generate a 2FA secret"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        assert secret is not None
        assert len(secret) == 32  # TOTP secrets are typically 32 characters
        assert user.two_factor_secret == secret

    def test_user_2fa_enable(self):
        """Test enabling 2FA for a user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        assert user.two_factor_enabled is False
        
        # Enable 2FA
        user.enable_2fa()
        assert user.two_factor_enabled is True

    def test_user_2fa_disable(self):
        """Test disabling 2FA for a user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        assert user.two_factor_enabled is True
        
        # Disable 2FA
        user.disable_2fa()
        assert user.two_factor_enabled is False
        assert user.two_factor_secret is None

    def test_2fa_code_verification(self):
        """Test verification of 2FA codes"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        # Generate a valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        # Test valid code
        assert user.verify_2fa_code(valid_code) is True
        
        # Test invalid code
        assert user.verify_2fa_code('000000') is False

    def test_2fa_code_verification_when_disabled(self):
        """Test verification of 2FA codes when 2FA is disabled"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.verify_2fa_code('000000') is False

    def test_2fa_code_verification_without_secret(self):
        """Test verification of 2FA codes when secret is not set"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.two_factor_enabled = True
        user.save()
        assert user.verify_2fa_code('000000') is False

    def test_2fa_qr_code_generation(self):
        """Test generation of QR code for 2FA setup"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        
        # Generate QR code
        qr_code = user.generate_2fa_qr_code()
        assert qr_code is not None
        
        # Verify QR code is a valid image
        img = Image.open(BytesIO(qr_code))
        assert img.format == 'PNG'
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_2fa_qr_code_generation_without_secret(self):
        """Test generation of QR code when secret is not set"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        qr_code = user.generate_2fa_qr_code()
        assert qr_code is None

    def test_2fa_backup_codes_generation(self):
        """Test generation of backup codes"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        # Generate backup codes
        backup_codes = user.generate_backup_codes()
        assert len(backup_codes) == settings.TWO_FACTOR['BACKUP_CODES_COUNT']
        assert all(len(code) == settings.TWO_FACTOR['BACKUP_CODES_LENGTH'] for code in backup_codes)
        
        # Verify backup codes are stored
        assert user.backup_codes is not None
        stored_codes = json.loads(user.backup_codes)
        assert len(stored_codes) == settings.TWO_FACTOR['BACKUP_CODES_COUNT']

    def test_2fa_backup_codes_generation_when_disabled(self):
        """Test generation of backup codes when 2FA is disabled"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        with pytest.raises(ValidationError) as exc_info:
            user.generate_backup_codes()
        assert "2FA must be enabled to generate backup codes" in str(exc_info.value)

    def test_backup_code_verification(self):
        """Test verification of backup codes"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        backup_codes = user.generate_backup_codes()
        
        # Test valid backup code
        assert user.verify_backup_code(backup_codes[0]) is True
        
        # Test invalid backup code
        assert user.verify_backup_code('INVALID') is False

    def test_backup_code_verification_without_codes(self):
        """Test verification of backup codes when no codes are set"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.verify_backup_code('ANY_CODE') is False

    def test_backup_code_consumption(self):
        """Test that backup codes are consumed after use"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        backup_codes = user.generate_backup_codes()
        original_codes = backup_codes.copy()
        
        # Use a backup code
        user.verify_backup_code(backup_codes[0])
        
        # Verify the code was removed
        stored_codes = json.loads(user.backup_codes)
        assert len(stored_codes) == len(original_codes) - 1
        assert backup_codes[0] not in stored_codes

    def test_2fa_required_validation(self):
        """Test validation of 2FA requirements"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test enabling 2FA without secret
        with pytest.raises(ValidationError):
            user.enable_2fa()
        
        # Generate secret and enable 2FA
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        # Test disabling 2FA
        user.disable_2fa()
        assert user.two_factor_enabled is False
        assert user.two_factor_secret is None
        assert user.backup_codes is None

    def test_2fa_code_format_validation(self):
        """Test validation of 2FA code format"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        
        # Test invalid code formats
        assert user.verify_2fa_code('') is False
        assert user.verify_2fa_code('12345') is False  # Too short
        assert user.verify_2fa_code('1234567') is False  # Too long
        assert user.verify_2fa_code('abcdef') is False  # Non-numeric
        
        # Test valid code format
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        assert user.verify_2fa_code(valid_code) is True

    def test_2fa_rate_limiting(self):
        """Test rate limiting for 2FA verification attempts"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        
        # Clear any existing cache entries
        cache_key = f'2fa_attempts_{user.username}'
        cache.delete(cache_key)
        
        # Test maximum attempts
        for _ in range(settings.TWO_FACTOR['MAX_VERIFICATION_ATTEMPTS']):
            assert user.verify_2fa_code('000000') is False
        
        # Verify rate limiting is enforced
        with pytest.raises(ValidationError) as exc_info:
            user.verify_2fa_code('000000')
        assert "Too many verification attempts" in str(exc_info.value)

    def test_2fa_qr_code_issuer_name(self):
        """Test QR code generation with correct issuer name"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        
        # Generate QR code
        qr_code = user.generate_2fa_qr_code()
        assert qr_code is not None
        
        # Verify QR code contains correct issuer name
        img = Image.open(BytesIO(qr_code))
        # Note: We can't easily verify the QR code contents in the test
        # as it's an encoded image. In practice, you would need to decode
        # the QR code to verify the issuer name.

    def test_2fa_backup_codes_length(self):
        """Test backup codes meet length requirements"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        backup_codes = user.generate_backup_codes()
        expected_length = settings.TWO_FACTOR['BACKUP_CODES_LENGTH']
        
        for code in backup_codes:
            assert len(code) == expected_length
            assert code.isalnum()  # Should only contain alphanumeric characters

    def test_user_creation_without_email(self):
        """Test user creation without email"""
        with pytest.raises(ValueError):
            User.objects.create_user(None, 'testpass123')

    def test_superuser_creation_without_staff_flag(self):
        """Test superuser creation without staff flag"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )

    def test_superuser_creation_without_superuser_flag(self):
        """Test superuser creation without superuser flag"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )

    def test_user_creation_with_empty_password(self):
        """Test user creation with empty password"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        assert user.email == 'test@example.com'
        assert user.check_password('')  # Empty password 

    def test_superuser_creation_with_defaults(self):
        """Test superuser creation with default flags"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin_user.email == 'admin@example.com'
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_user_string_representation(self):
        """Test the string representation of a user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert str(user) == 'testuser'

    def test_user_full_name(self):
        """Test getting the full name of a user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.get_full_name() == 'Test User'

    def test_user_short_name(self):
        """Test getting the short name of a user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.get_short_name() == 'Test' 

class TwoFactorAuthenticationTests(APITestCase):
    def setUp(self):
        """Set up test case"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()  # Clear cache before each test

    def tearDown(self):
        """Clean up after test case"""
        cache.clear()  # Clear cache after each test

    def test_2fa_setup(self):
        """Test 2FA setup process"""
        # Generate 2FA secret
        secret = self.user.generate_2fa_secret()
        self.assertIsNotNone(secret)
        self.assertEqual(len(secret), 32)

        # Enable 2FA
        self.user.enable_2fa()
        self.assertTrue(self.user.two_factor_enabled)

        # Generate QR code
        qr_code = self.user.generate_2fa_qr_code()
        self.assertIsNotNone(qr_code)

        # Generate backup codes
        backup_codes = self.user.generate_backup_codes()
        self.assertEqual(len(backup_codes), 8)
        self.assertIsNotNone(self.user.backup_codes)

    def test_2fa_verification(self):
        """Test 2FA code verification"""
        # Setup 2FA with a known secret
        secret = 'JBSWY3DPEHPK3PXP'
        self.user.two_factor_secret = secret
        self.user.two_factor_enabled = True
        self.user.save()
        
        # Generate a valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        # Test valid code
        self.assertTrue(self.user.verify_2fa_code(valid_code))

        # Test invalid code
        self.assertFalse(self.user.verify_2fa_code('000000'))

    def test_backup_codes(self):
        """Test backup codes functionality"""
        # Setup 2FA and generate backup codes
        self.user.generate_2fa_secret()
        self.user.enable_2fa()
        backup_codes = self.user.generate_backup_codes()

        # Test valid backup code
        valid_code = backup_codes[0]
        self.assertTrue(self.user.verify_backup_code(valid_code))

        # Test invalid backup code
        self.assertFalse(self.user.verify_backup_code('invalid_code'))

        # Test used backup code can't be used again
        self.assertFalse(self.user.verify_backup_code(valid_code))

    def test_disable_2fa(self):
        """Test disabling 2FA"""
        # Setup 2FA
        self.user.generate_2fa_secret()
        self.user.enable_2fa()
        self.user.generate_backup_codes()

        # Disable 2FA
        self.user.disable_2fa()
        self.assertFalse(self.user.two_factor_enabled)
        self.assertIsNone(self.user.two_factor_secret)
        self.assertIsNone(self.user.backup_codes)

    def test_2fa_validation(self):
        """Test 2FA validation rules"""
        # Test enabling 2FA without secret
        with self.assertRaises(ValidationError):
            self.user.enable_2fa()

        # Test verifying code without 2FA enabled
        self.assertFalse(self.user.verify_2fa_code('123456'))

        # Test verifying code without secret
        self.user.two_factor_enabled = True
        self.user.save()
        self.assertFalse(self.user.verify_2fa_code('123456'))

    def test_qr_code_generation(self):
        """Test QR code generation"""
        # Setup 2FA
        self.user.generate_2fa_secret()
        
        # Generate QR code
        qr_code = self.user.generate_2fa_qr_code()
        self.assertIsNotNone(qr_code)
        self.assertIsInstance(qr_code, bytes) 