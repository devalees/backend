from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from Apps.core.mixins import ImportExportMixin
from django.apps import apps
from django.db.models import Q

User = get_user_model()

def get_enabled_models():
    """Get all models that have import/export enabled."""
    enabled_models = []
    for model in ContentType.objects.all():
        model_class = model.model_class()
        if model_class and hasattr(model_class, 'is_import_export_enabled'):
            if model_class.is_import_export_enabled():
                enabled_models.append(model.model)
    return enabled_models

def get_content_type_choices():
    """Get list of content types that support import/export operations."""
    choices = Q()
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            if hasattr(model, 'supports_import_export') and model.supports_import_export:
                content_type = ContentType.objects.get_for_model(model)
                choices |= Q(id=content_type.id)
    return choices

class ImportExportConfig(models.Model):
    """Configuration for import/export operations."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=get_content_type_choices
    )
    field_mapping = models.JSONField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_import_export_configs'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_import_export_configs'
    )

    class Meta:
        unique_together = ('name', 'content_type')
        ordering = ['-created_at']
        permissions = [
            ('manage_import_export', 'Can manage import/export configurations and logs'),
        ]

    def __str__(self):
        return f"{self.name} ({self.content_type.model})"

    def clean(self):
        """Validate the configuration."""
        super().clean()
        
        # Validate content type
        model_class = self.content_type.model_class()
        if not model_class or not hasattr(model_class, 'supports_import_export') or not model_class.supports_import_export:
            raise ValidationError('Selected model does not support import/export operations')
        
        # Validate field mapping
        if not isinstance(self.field_mapping, dict):
            raise ValidationError('Field mapping must be a dictionary')
        
        if not self.field_mapping:
            raise ValidationError('Field mapping cannot be empty')
        
        # Validate field names
        model_fields = [f.name for f in model_class._meta.get_fields()]
        for source, target in self.field_mapping.items():
            if target not in model_fields:
                raise ValidationError(f'Invalid target field: {target}')

        # Check for unique name per content type
        if ImportExportConfig.objects.filter(
            name=self.name,
            content_type=self.content_type
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('A configuration with this name already exists for this model.'))

class ImportExportLog(models.Model):
    """
    Model for tracking import/export operations.
    """
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed')
    ]

    OPERATION_IMPORT = 'import'
    OPERATION_EXPORT = 'export'
    OPERATION_CHOICES = [
        (OPERATION_IMPORT, 'Import'),
        (OPERATION_EXPORT, 'Export')
    ]

    config = models.ForeignKey(ImportExportConfig, on_delete=models.CASCADE)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    file_name = models.CharField(max_length=255)
    error_message = models.TextField(blank=True, default='')
    records_processed = models.IntegerField(default=0)
    records_succeeded = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']  # Order by creation date (newest first) and then by ID
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['performed_by']),
        ]

    def clean(self):
        """Validate the log."""
        super().clean()
        
        # Validate record counts
        if self.records_processed < 0:
            raise ValidationError('Records processed cannot be negative.')
        if self.records_succeeded < 0:
            raise ValidationError('Records succeeded cannot be negative.')
        if self.records_failed < 0:
            raise ValidationError('Records failed cannot be negative.')
        if self.records_succeeded + self.records_failed > self.records_processed:
            raise ValidationError('Sum of succeeded and failed records cannot exceed total processed records.')
        
        # Validate status changes
        if self.pk:  # Only check on updates
            original = ImportExportLog.objects.get(pk=self.pk)
            if original.status == self.STATUS_COMPLETED and self.status != self.STATUS_COMPLETED:
                raise ValidationError('Cannot change status of a completed log.')

    def save(self, *args, **kwargs):
        """Save the log."""
        if not hasattr(self, '_original_status'):
            self._original_status = self.status
        super().save(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        return f"{self.operation.title()}: {self.file_name} ({self.status})"

    @property
    def is_failed(self):
        """Check if the operation failed."""
        return self.status == self.STATUS_FAILED
        
    @property
    def success_rate(self):
        """Calculate the success rate as a percentage."""
        if self.records_processed == 0:
            return 0.0
        return (self.records_succeeded / self.records_processed) * 100.0

class TestModel(models.Model, ImportExportMixin):
    """Test model for import/export functionality."""
    supports_import_export = True
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_test_models'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_test_models'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class NonImportExportModel(models.Model):
    """Model that does not support import/export operations."""
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
