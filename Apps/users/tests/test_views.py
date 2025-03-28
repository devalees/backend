import pytest
import pyotp
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch, MagicMock
from Apps.users.models import User

User = get_user_model()

@pytest.mark.django_db
class TestTwoFactorViews:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def authenticated_client(self, client, user):
        client.login(username='testuser', password='testpass123')
        return client

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down for each test"""
        cache.clear()  # Clear cache before each test
        yield
        cache.clear()  # Clear cache after each test

    def test_2fa_page_access(self, authenticated_client):
        """Test accessing the 2FA page"""
        response = authenticated_client.get(reverse('2fa_page'))
        assert response.status_code == 200
        assert 'Setup 2FA' in response.content.decode()

    def test_2fa_page_requires_login(self, client):
        """Test that 2FA page requires login"""
        response = client.get(reverse('2fa_page'))
        assert response.status_code == 302  # Redirects to login page

    def test_setup_2fa(self, authenticated_client):
        """Test 2FA setup process"""
        response = authenticated_client.post(reverse('setup_2fa'))
        assert response.status_code == 200
        assert 'qr_code' in response.context
        assert 'secret' in response.context

    def test_verify_2fa(self, authenticated_client, user):
        """Test 2FA verification"""
        # First setup 2FA
        authenticated_client.post(reverse('setup_2fa'))
        
        # Refresh user instance to get the new secret
        user.refresh_from_db()
        
        # Generate a valid TOTP code
        totp = pyotp.TOTP(user.two_factor_secret)
        valid_code = totp.now()
        
        # Verify the code
        response = authenticated_client.post(
            reverse('verify_2fa'),
            {'code': valid_code},
            follow=True  # Follow redirects
        )
        
        # Refresh user instance to check if 2FA is enabled
        user.refresh_from_db()
        assert user.two_factor_enabled
        assert response.status_code == 200  # After following redirect
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert '2FA has been enabled successfully' in str(messages[0])

    def test_verify_2fa_invalid_code(self, authenticated_client):
        """Test 2FA verification with invalid code"""
        # First setup 2FA
        authenticated_client.post(reverse('setup_2fa'))
        
        # Try with invalid code
        response = authenticated_client.post(
            reverse('verify_2fa'),
            {'code': '000000'},
            follow=True  # Follow redirects
        )
        assert response.status_code == 200
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert 'Invalid verification code' in str(messages[0])

    def test_verify_2fa_rate_limiting(self, authenticated_client):
        """Test rate limiting for 2FA verification"""
        # First setup 2FA
        response = authenticated_client.post(reverse('setup_2fa'))
        
        # Try multiple times with invalid code
        for _ in range(settings.TWO_FACTOR['MAX_VERIFICATION_ATTEMPTS'] + 1):
            response = authenticated_client.post(
                reverse('verify_2fa'),
                {'code': '000000'},
                follow=True
            )
            
            # Check if we've hit the rate limit
            if 'Too many verification attempts' in str(list(response.context['messages'])[0]):
                break
        
        assert response.status_code == 200
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert 'Too many verification attempts' in str(messages[0])

    def test_disable_2fa(self, authenticated_client, user):
        """Test disabling 2FA"""
        # First setup and enable 2FA
        authenticated_client.post(reverse('setup_2fa'))
        
        # Refresh user instance to get the new secret
        user.refresh_from_db()
        
        totp = pyotp.TOTP(user.two_factor_secret)
        authenticated_client.post(
            reverse('verify_2fa'),
            {'code': totp.now()},
            follow=True  # Follow redirects
        )
        
        # Now disable 2FA
        response = authenticated_client.post(
            reverse('disable_2fa'),
            follow=True  # Follow redirects
        )
        
        # Refresh user instance to verify 2FA is disabled
        user.refresh_from_db()
        assert not user.two_factor_enabled
        assert not user.two_factor_secret
        assert response.status_code == 200  # After following redirect
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert '2FA disabled successfully' in str(messages[0])

    def test_generate_backup_codes(self, authenticated_client, user):
        """Test generating backup codes"""
        # First setup and enable 2FA
        authenticated_client.post(reverse('setup_2fa'))
        
        # Refresh user instance to get the new secret
        user.refresh_from_db()
        
        totp = pyotp.TOTP(user.two_factor_secret)
        authenticated_client.post(
            reverse('verify_2fa'),
            {'code': totp.now()},
            follow=True  # Follow redirects
        )
        
        # Generate backup codes
        response = authenticated_client.post(
            reverse('generate_backup_codes'),
            follow=True  # Follow redirects
        )
        assert response.status_code == 200
        assert 'backup_codes' in response.context
        assert len(response.context['backup_codes']) == settings.TWO_FACTOR['BACKUP_CODES_COUNT']

    def test_generate_backup_codes_when_disabled(self, authenticated_client):
        """Test generating backup codes when 2FA is disabled"""
        response = authenticated_client.post(
            reverse('generate_backup_codes'),
            follow=True  # Follow redirects
        )
        assert response.status_code == 200
        messages = list(response.context['messages'])
        assert len(messages) > 0
        assert '2FA must be enabled' in str(messages[0]) 