from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from Apps.data_transfer.mixins import DynamicDownloadMixin

User = get_user_model()

class ContactType(models.TextChoices):
    ENTITY = 'entity', 'Entity'
    INDIVIDUAL = 'individual', 'Individual'

class ContactCategory(DynamicDownloadMixin, models.Model):
    """Model for categorizing contacts"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_contact_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Contact Category"
        verbose_name_plural = "Contact Categories"

    @classmethod
    def get_default_category(cls):
        """Get or create the default category"""
        default_category, created = cls.objects.get_or_create(
            name='Default',
            defaults={
                'description': 'Default category for contacts',
                'is_active': True
            }
        )
        return default_category

    def save(self, *args, **kwargs):
        """Override save to prevent creating another default category"""
        if self.name == 'Default' and not self.pk:
            if ContactCategory.objects.filter(name='Default').exists():
                raise ValidationError("A default category already exists")
        super().save(*args, **kwargs)

class Contact(DynamicDownloadMixin, models.Model):
    """Contact model for storing contact form submissions"""
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(
        max_length=255,
        validators=[EmailValidator()],
        blank=True,
        null=True
    )
    contact_type = models.CharField(
        max_length=20,
        choices=ContactType.choices,
        default=ContactType.INDIVIDUAL
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    company = models.CharField(max_length=200, blank=True, null=True)
    category = models.ForeignKey(
        'ContactCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts'
    )
    message = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,  # Allow null for system-generated contacts
        blank=True, # Make it optional in forms
        related_name='created_contacts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        category_str = f" - {self.category.name}" if self.category else ""
        email_str = f" ({self.email})" if self.email else ""
        return f"{self.first_name} {self.last_name}{email_str}{category_str}"

    def clean(self):
        """Custom validation"""
        super().clean()
        if self.phone and not self.phone.startswith('+'):
            self.phone = '+' + self.phone
        if self.contact_type not in ContactType.values:
            raise ValidationError(f"Invalid contact type. Must be one of {ContactType.values}")

    def save(self, *args, **kwargs):
        """Override save to ensure clean is called and set default category"""
        # Skip full_clean in tests or when importing data
        if not kwargs.pop('skip_validation', False):
            self.full_clean()
        
        if not self.category:
            self.category = ContactCategory.get_default_category()
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
