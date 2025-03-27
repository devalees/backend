from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

class ContactType(models.TextChoices):
    ENTITY = 'entity', 'Entity'
    INDIVIDUAL = 'individual', 'Individual'

class ContactCategory(models.Model):
    """Model for categorizing contacts"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Contact Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

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

class Contact(models.Model):
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
        ContactCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        default=ContactCategory.get_default_category
    )
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

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
        """Override save to ensure clean is called"""
        self.full_clean()
        super().save(*args, **kwargs)
