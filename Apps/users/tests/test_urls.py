from django.test import TestCase
from django.urls import reverse

class TestTwoFactorURLs(TestCase):
    def test_2fa_page_url(self):
        """Test 2FA page URL"""
        url = reverse('2fa_page')
        assert url == '/users/2fa/'

    def test_setup_2fa_url(self):
        """Test setup 2FA URL"""
        url = reverse('setup_2fa')
        assert url == '/users/2fa/setup/'

    def test_verify_2fa_url(self):
        """Test verify 2FA URL"""
        url = reverse('verify_2fa')
        assert url == '/users/2fa/verify/'

    def test_disable_2fa_url(self):
        """Test disable 2FA URL"""
        url = reverse('disable_2fa')
        assert url == '/users/2fa/disable/'

    def test_generate_backup_codes_url(self):
        """Test generate backup codes URL"""
        url = reverse('generate_backup_codes')
        assert url == '/users/2fa/backup-codes/' 