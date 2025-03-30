from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .mixins import ImportExportMixin

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

class ImportExportConfig(models.Model):
    """Configuration for import/export operations."""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=lambda: {'model__in': get_enabled_models()}
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

    def __str__(self):
        return f"{self.name} ({self.content_type.model})"

    def clean(self):
        """Validate the configuration."""
        if not self.content_type.model_class().is_import_export_enabled():
            raise ValidationError(_('This model does not support import/export operations.'))
        if not isinstance(self.field_mapping, dict):
            raise ValidationError(_('Field mapping must be a dictionary.'))
        if not self.field_mapping:
            raise ValidationError(_('Field mapping cannot be empty.'))
            
        # Check for unique name per content type
        if ImportExportConfig.objects.filter(
            name=self.name,
            content_type=self.content_type
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('A configuration with this name already exists for this model.'))

class ImportExportLog(models.Model):
    """Log entry for import/export operations."""
    
    OPERATION_IMPORT = 'import'
    OPERATION_EXPORT = 'export'
    OPERATION_CHOICES = [
        (OPERATION_IMPORT, _('Import')),
        (OPERATION_EXPORT, _('Export')),
    ]
    
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_FAILED, _('Failed')),
    ]
    
    config = models.ForeignKey(ImportExportConfig, on_delete=models.CASCADE)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    file_name = models.CharField(max_length=255)
    error_message = models.TextField(blank=True, null=True)
    records_processed = models.IntegerField(default=0)
    records_succeeded = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

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

    def clean(self):
        """Validate the log entry."""
        if self.records_succeeded + self.records_failed != self.records_processed:
            raise ValidationError(_('Sum of succeeded and failed records must equal total processed.'))
        
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError(_('Invalid status value.'))
            
        # Validate status transitions
        if self.pk:  # Only check transitions for existing records
            old_instance = ImportExportLog.objects.get(pk=self.pk)
            if old_instance.status == self.STATUS_COMPLETED and self.status != self.STATUS_COMPLETED:
                raise ValidationError(_('Cannot change status of a completed log.'))
            if old_instance.status == self.STATUS_FAILED and self.status not in [self.STATUS_FAILED, self.STATUS_IN_PROGRESS]:
                raise ValidationError(_('Failed logs can only be retried or remain failed.'))
