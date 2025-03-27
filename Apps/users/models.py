from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.conf import settings
import pyotp
import qrcode
import secrets
import json
from io import BytesIO
import re
import random
import string
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class UserGroup(models.Model):
    """Through model for User-Group relationship"""
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        app_label = 'users'
        db_table = 'users_user_groups'
        unique_together = ('user', 'group')

class CustomUserManager(BaseUserManager):
    """Custom user model manager where username is the unique identifier"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a User with the given username, email and password."""
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        username = self.model.normalize_username(username)
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password if password is not None else '')
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given username, email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for testing"""

    class Meta:
        app_label = 'users'
        swappable = 'AUTH_USER_MODEL'
        db_table = 'users_user'

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    two_factor_secret = models.CharField(max_length=32, null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    backup_codes = models.TextField(null=True, blank=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
        through=UserGroup
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def generate_2fa_secret(self):
        """Generate a new 2FA secret for the user"""
        secret = pyotp.random_base32()
        self.two_factor_secret = secret
        self.save()
        return secret

    def enable_2fa(self):
        """Enable 2FA for the user"""
        if not self.two_factor_secret:
            raise ValidationError("2FA secret must be generated before enabling 2FA")
        self.two_factor_enabled = True
        self.save()

    def disable_2fa(self):
        """Disable 2FA for the user"""
        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.backup_codes = None
        self.save()

    def verify_2fa_code(self, code):
        """Verify a 2FA code with rate limiting and format validation"""
        # Check rate limiting
        cache_key = f'2fa_attempts_{self.username}'
        attempts = cache.get(cache_key, 0)
        
        if attempts >= settings.TWO_FACTOR['MAX_VERIFICATION_ATTEMPTS']:
            raise ValidationError("Too many verification attempts. Please try again later.")
        
        # Validate code format
        if not code or not re.match(r'^\d{6}$', code):
            cache.set(cache_key, attempts + 1, settings.TWO_FACTOR['VERIFICATION_TIMEOUT'])
            return False
        
        if not self.two_factor_secret:
            return False
            
        totp = pyotp.TOTP(self.two_factor_secret)
        is_valid = totp.verify(code)
        
        if not is_valid:
            cache.set(cache_key, attempts + 1, settings.TWO_FACTOR['VERIFICATION_TIMEOUT'])
        else:
            cache.delete(cache_key)
            
        return is_valid

    def generate_2fa_qr_code(self):
        """Generate a QR code for 2FA setup"""
        if not self.two_factor_secret:
            return None
        
        # Create the provisioning URI
        provisioning_uri = pyotp.totp.TOTP(self.two_factor_secret).provisioning_uri(
            self.username,
            issuer_name=settings.TWO_FACTOR['ISSUER_NAME']
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=settings.TWO_FACTOR['QR_CODE_SIZE'],
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    def generate_backup_codes(self):
        """Generate new backup codes for 2FA"""
        if not self.two_factor_enabled:
            raise ValidationError("2FA must be enabled to generate backup codes")

        # Generate random backup codes
        backup_codes = []
        for _ in range(settings.TWO_FACTOR['BACKUP_CODES_COUNT']):
            code = ''.join(random.choices(string.digits, k=settings.TWO_FACTOR['BACKUP_CODES_LENGTH']))
            backup_codes.append(code)

        # Store hashed backup codes
        self.backup_codes = json.dumps([make_password(code) for code in backup_codes])
        self.save()

        return backup_codes

    def verify_backup_code(self, code):
        """Verify a backup code"""
        if not self.backup_codes:
            return False

        try:
            stored_codes = json.loads(self.backup_codes)
            for stored_code in stored_codes:
                if check_password(code, stored_code):
                    # Remove used code
                    stored_codes.remove(stored_code)
                    self.backup_codes = json.dumps(stored_codes)
                    self.save()
                    return True
            return False
        except json.JSONDecodeError:
            return False
