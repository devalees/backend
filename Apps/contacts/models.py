from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from Apps.core.models import TaskAwareModel
from Apps.entity.models import Organization, Department, Team
import re
from django.db.models.signals import pre_save
from django.dispatch import receiver

User = get_user_model()

class Contact(TaskAwareModel):
    """Contact model representing a person or organization with task handling capabilities"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_updated'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'entity.Department',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    team = models.ForeignKey(
        'entity.Team',
        on_delete=models.CASCADE,
        related_name='contacts',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            self.full_clean()
        super().save(*args, **kwargs)

    def hard_delete(self):
        """Hard delete the contact"""
        self.delete(hard_delete=True)

    def delete(self, *args, **kwargs):
        """Delete the contact"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def clean(self):
        """Validate contact data"""
        # Validate email format
        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError({'email': ['Enter a valid email address.']})

        # Validate phone format (simple validation for demonstration)
        phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
        if not phone_pattern.match(self.phone):
            raise ValidationError({'phone': ['Enter a valid phone number (9-15 digits, optionally starting with + and country code).']})

        # Validate department belongs to organization
        if self.department and self.department.organization != self.organization:
            raise ValidationError({'department': ['Department must belong to the contact\'s organization.']})

        # Validate team belongs to department
        if self.team:
            if not self.department:
                raise ValidationError({'team': ['Cannot assign team without department.']})
            if self.team.department != self.department:
                raise ValidationError({'team': ['Team must belong to the contact\'s department.']})

class ContactGroup(models.Model):
    """ContactGroup model representing a group of contacts"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_groups_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_groups_updated'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='contact_groups',
        null=True,
        blank=True
    )
    contacts = models.ManyToManyField(
        Contact,
        related_name='groups',
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Contact Group'
        verbose_name_plural = 'Contact Groups'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the contact group"""
        super().save(*args, **kwargs)
        if hasattr(self, '_contacts'):
            self.contacts.set(self._contacts)

    def clean(self):
        """Validate the contact group"""
        super().clean()
        if self.pk and self.contacts.exists():
            # Check if all contacts belong to the same organization
            contacts_orgs = self.contacts.values_list('organization', flat=True).distinct()
            if len(contacts_orgs) > 1 or (len(contacts_orgs) == 1 and contacts_orgs[0] != self.organization.id):
                raise ValidationError("All contacts must belong to the same organization as the group.")

    def delete(self, *args, **kwargs):
        """Delete the contact group"""
        hard_delete = kwargs.pop('hard_delete', False)
        if hard_delete:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def hard_delete(self):
        """Hard delete the contact group"""
        self.delete(hard_delete=True)
