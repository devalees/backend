import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from Apps.users.tests.factories import UserFactory
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import pyotp
from django.conf import settings

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory(is_superuser=True)
    api_client.force_authenticate(user=user)
    return api_client

@pytest.mark.django_db
class TestUserViewSet:
    def test_list_users(self, authenticated_client):
        """Test listing users"""
        # Get the authenticated user (superuser) from the client
        superuser = authenticated_client.handler._force_user
        
        # Create test users with proper created_by field
        users = [UserFactory(created_by=superuser) for _ in range(3)]
        
        url = reverse('users:users-list')
        response = authenticated_client.get(url, {'ordering': 'id'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 3
        
        # Verify created_by field in response
        for user_data in response.data['results']:
            if user_data['id'] != superuser.id:  # Skip the superuser itself
                assert user_data['created_by'] == superuser.id

    def test_create_user(self, authenticated_client):
        """Test creating a user"""
        # Get the authenticated user (superuser) from the client
        superuser = authenticated_client.handler._force_user
        
        url = reverse('users:users-list')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'created_by': superuser.id  # Add created_by field
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email=data['email']).exists()
        created_user = User.objects.get(email=data['email'])
        assert created_user.created_by == superuser

    def test_retrieve_user(self, authenticated_client):
        """Test retrieving a user"""
        user = UserFactory()
        url = reverse('users:users-detail', kwargs={'pk': user.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_update_user(self, authenticated_client):
        """Test updating a user"""
        # Get the authenticated user (superuser) from the client
        superuser = authenticated_client.handler._force_user
        
        # Create a user with proper created_by field
        user = UserFactory(created_by=superuser)
        
        url = reverse('users:users-detail', kwargs={'pk': user.pk})
        data = {'first_name': 'Updated Name'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == data['first_name']
        assert user.created_by == superuser  # Ensure created_by wasn't changed

    def test_delete_user(self, authenticated_client):
        """Test deleting a user"""
        # Get the authenticated user (superuser) from the client
        superuser = authenticated_client.handler._force_user
        
        # Create a user with proper created_by field
        user = UserFactory(created_by=superuser)
        
        url = reverse('users:users-detail', kwargs={'pk': user.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user = User.objects.get(pk=user.pk)
        assert not user.is_active
        assert user.created_by == superuser  # Ensure created_by wasn't changed

    def test_login_success(self, api_client):
        """Test successful login"""
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        url = reverse('users:users-login')
        data = {
            'email': user.email,
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        url = reverse('users:users-login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_refresh_token_success(self, api_client):
        """Test successful token refresh"""
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        # First login to get tokens
        login_url = reverse('users:users-login')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Then refresh the token
        refresh_url = reverse('users:users-refresh-token')
        refresh_data = {'refresh': refresh_token}
        response = api_client.post(refresh_url, refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        """Test refresh token with invalid token"""
        url = reverse('users:users-refresh-token')
        data = {'refresh': 'invalid_token'}
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_logout_success(self, authenticated_client):
        """Test successful logout"""
        # First login to get tokens
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        login_url = reverse('users:users-login')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        login_response = authenticated_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Then logout
        logout_url = reverse('users:users-logout')
        logout_data = {'refresh': refresh_token}
        response = authenticated_client.post(logout_url, logout_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_password_reset_request(self, authenticated_client):
        """Test requesting a password reset."""
        user = UserFactory()
        response = authenticated_client.post(
            reverse('users:users-password-reset'),
            {'email': user.email}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert 'Password Reset Requested' in mail.outbox[0].subject

    def test_password_reset_request_invalid_email(self, authenticated_client):
        """Test requesting a password reset with invalid email."""
        response = authenticated_client.post(
            reverse('users:users-password-reset'),
            {'email': 'nonexistent@example.com'}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_password_reset_confirm(self, api_client):
        """Test confirming password reset with valid token."""
        # Create user with a known password
        user = UserFactory()
        user.set_password('oldpassword123')
        user.save()
        
        # Generate reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        print(f"\nDebug test: Generated uid={uid} for user_id={user.pk}")
        print(f"Debug test: Generated token={token}")
        
        new_password = 'newpassword123'
        data = {
            'uid': uid,
            'token': token,
            'new_password': new_password,
            'new_password2': new_password
        }
        print(f"Debug test: Sending data={data}")
        
        response = api_client.post(
            reverse('users:users-password-reset-confirm'),
            data
        )
        print(f"Debug test: Response status={response.status_code}")
        print(f"Debug test: Response data={response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password(new_password)

    def test_password_reset_confirm_invalid_token(self, api_client):
        """Test confirming password reset with invalid token."""
        user = UserFactory()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        response = api_client.post(
            reverse('users:users-password-reset-confirm'),
            {
                'uid': uid,
                'token': 'invalid_token',
                'new_password': 'newpassword123',
                'new_password2': 'newpassword123'  # Add password confirmation
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid or expired reset link' in response.data['error']
        assert not user.check_password('newpassword123')

    def test_login_with_2fa(self, api_client):
        """Test login flow with 2FA enabled"""
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        # Enable 2FA
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        # First login attempt
        login_url = reverse('users:users-login')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        response = api_client.post(login_url, login_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['requires_2fa'] is True
        assert 'user_id' in response.data
        
        # Verify 2FA code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        verify_url = reverse('users:users-verify-2fa')
        verify_data = {
            'user_id': response.data['user_id'],
            'code': code
        }
        response = api_client.post(verify_url, verify_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_enable_2fa(self, authenticated_client):
        """Test enabling 2FA"""
        # Create and authenticate user
        user = UserFactory()
        authenticated_client.force_authenticate(user=user)
        
        url = reverse('users:users-enable-2fa')
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'secret' in response.data
        assert 'qr_code' in response.data
        assert 'instructions' in response.data
        assert 'manual_entry_code' in response.data
        
        # Confirm 2FA
        totp = pyotp.TOTP(response.data['secret'])
        code = totp.now()
        
        confirm_url = reverse('users:users-confirm-2fa')
        confirm_data = {'code': code}
        response = authenticated_client.post(confirm_url, confirm_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '2FA has been enabled successfully'
        
        # Verify 2FA is enabled
        user.refresh_from_db()
        assert user.two_factor_enabled is True

    def test_disable_2fa(self, authenticated_client):
        """Test disabling 2FA"""
        # Create and authenticate user
        user = UserFactory()
        authenticated_client.force_authenticate(user=user)
        
        # First enable 2FA
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        # Generate valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # Disable 2FA
        url = reverse('users:users-disable-2fa')
        data = {'code': code}
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '2FA has been disabled successfully'
        
        # Verify 2FA is disabled
        user.refresh_from_db()
        assert user.two_factor_enabled is False
        assert user.two_factor_secret is None
        assert user.backup_codes == []

    def test_generate_backup_codes(self, authenticated_client):
        """Test generating backup codes"""
        # Create and authenticate user
        user = UserFactory()
        authenticated_client.force_authenticate(user=user)
        
        # First enable 2FA
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        
        url = reverse('users:users-generate-backup-codes')
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'backup_codes' in response.data
        assert len(response.data['backup_codes']) == 8  # As configured in settings

    def test_verify_backup_code(self, authenticated_client):
        """Test verifying backup codes"""
        # Create and authenticate user
        user = UserFactory()
        authenticated_client.force_authenticate(user=user)
        
        # First enable 2FA and generate backup codes
        secret = user.generate_2fa_secret()
        user.enable_2fa()
        backup_codes = user.generate_backup_codes()
        
        # Try to verify a backup code
        url = reverse('users:users-verify-backup-code')
        data = {'code': backup_codes[0]}
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Backup code verified successfully'
        
        # Verify the code was used (removed from backup codes)
        user.refresh_from_db()
        assert backup_codes[0] not in user.backup_codes

    def test_invalid_2fa_code(self, authenticated_client):
        """Test disabling 2FA with invalid code"""
        user = UserFactory()
        user.generate_2fa_secret()  # Generate secret first
        user.enable_2fa()
        authenticated_client.force_authenticate(user=user)
        
        url = reverse('users:users-disable-2fa')
        response = authenticated_client.post(url, {'code': '000000'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid 2FA code' in response.data['error']

    def test_rate_limiting_2fa(self, authenticated_client):
        """Test rate limiting for 2FA verification"""
        user = UserFactory()
        user.generate_2fa_secret()  # Generate secret first
        user.enable_2fa()
        authenticated_client.force_authenticate(user=user)
        
        url = reverse('users:users-disable-2fa')
        
        # Make multiple attempts with invalid codes
        for _ in range(settings.TWO_FACTOR['MAX_VERIFICATION_ATTEMPTS'] + 1):
            response = authenticated_client.post(url, {'code': '000000'})
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'Too many verification attempts' in response.data['error'] 