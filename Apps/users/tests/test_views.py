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
        users = [UserFactory() for _ in range(3)]
        url = reverse('user-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 3

    def test_create_user(self, authenticated_client):
        """Test creating a user"""
        url = reverse('user-list')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email=data['email']).exists()

    def test_retrieve_user(self, authenticated_client):
        """Test retrieving a user"""
        user = UserFactory()
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_update_user(self, authenticated_client):
        """Test updating a user"""
        user = UserFactory()
        url = reverse('user-detail', kwargs={'pk': user.pk})
        data = {'first_name': 'Updated Name'}
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == data['first_name']

    def test_delete_user(self, authenticated_client):
        """Test deleting a user"""
        user = UserFactory()
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        user = User.objects.get(pk=user.pk)
        assert not user.is_active

    def test_login_success(self, api_client):
        """Test successful login"""
        user = UserFactory()
        user.set_password('testpass123')
        user.save()
        
        url = reverse('user-login')
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
        url = reverse('user-login')
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
        login_url = reverse('user-login')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Then refresh the token
        refresh_url = reverse('user-refresh-token')
        refresh_data = {'refresh': refresh_token}
        response = api_client.post(refresh_url, refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        """Test refresh token with invalid token"""
        url = reverse('user-refresh-token')
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
        
        login_url = reverse('user-login')
        login_data = {
            'email': user.email,
            'password': 'testpass123'
        }
        login_response = authenticated_client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Then logout
        logout_url = reverse('user-logout')
        logout_data = {'refresh': refresh_token}
        response = authenticated_client.post(logout_url, logout_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_password_reset_request(self, authenticated_client):
        """Test requesting a password reset."""
        user = UserFactory()
        response = authenticated_client.post(
            reverse('users:password-reset'),
            {'email': user.email}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Password Reset Requested', mail.outbox[0].subject)

    def test_password_reset_request_invalid_email(self, authenticated_client):
        """Test requesting a password reset with invalid email."""
        response = authenticated_client.post(
            reverse('users:password-reset'),
            {'email': 'nonexistent@example.com'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset_confirm(self, authenticated_client):
        """Test confirming password reset."""
        user = UserFactory()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        new_password = 'newpassword123'
        response = authenticated_client.post(
            reverse('users:password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': new_password
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

    def test_password_reset_confirm_invalid_token(self, authenticated_client):
        """Test confirming password reset with invalid token."""
        user = UserFactory()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        response = authenticated_client.post(
            reverse('users:password-reset-confirm'),
            {
                'uid': uid,
                'token': 'invalid_token',
                'new_password': 'newpassword123'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 