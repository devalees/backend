from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from Apps.core.models import BaseModel

User = get_user_model()


class ImportExportConfig(BaseModel):
    """
    Configuration for import/export operations.
    Stores settings and preferences for different content types.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text=_('Content type this configuration applies to')
    )
    name = models.CharField(
        max_length=255,
        help_text=_('Name of this configuration')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Description of this configuration')
    )
    field_mapping = models.JSONField(
        help_text=_('JSON mapping of model fields to import/export fields'),
        blank=False,
        null=False
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this configuration is active')
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_configs'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_configs'
    )

    class Meta:
        verbose_name = _('Import Export Configuration')
        verbose_name_plural = _('Import Export Configurations')
        unique_together = ('content_type', 'name')
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the configuration."""
        super().clean()
        if not self.field_mapping:
            raise ValidationError({
                'field_mapping': _('Field mapping cannot be empty')
            })
        if not isinstance(self.field_mapping, dict):
            raise ValidationError({
                'field_mapping': _('Field mapping must be a dictionary')
            })


class ImportExportLog(BaseModel):
    """
    Log of import/export operations.
    Tracks all import/export activities for audit purposes.
    """
    OPERATION_IMPORT = 'import'
    OPERATION_EXPORT = 'export'
    OPERATION_CHOICES = [
        (OPERATION_IMPORT, _('Import')),
        (OPERATION_EXPORT, _('Export')),
    ]

    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_FAILED, _('Failed')),
    ]

    config = models.ForeignKey(
        ImportExportConfig,
        on_delete=models.PROTECT,
        related_name='logs',
        help_text=_('Configuration used for this operation')
    )
    operation = models.CharField(
        max_length=10,
        choices=OPERATION_CHOICES,
        help_text=_('Type of operation performed')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text=_('Current status of the operation')
    )
    file_name = models.CharField(
        max_length=255,
        help_text=_('Name of the file processed')
    )
    error_message = models.TextField(
        blank=True,
        help_text=_('Error message if operation failed')
    )
    records_processed = models.IntegerField(
        default=0,
        help_text=_('Number of records processed')
    )
    records_succeeded = models.IntegerField(
        default=0,
        help_text=_('Number of records successfully processed')
    )
    records_failed = models.IntegerField(
        default=0,
        help_text=_('Number of records that failed processing')
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_export_logs',
        help_text=_('User who performed the operation')
    )

    class Meta:
        verbose_name = _('Import Export Log')
        verbose_name_plural = _('Import Export Logs')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.get_operation_display()}: {self.file_name} ({self.get_status_display().lower()})"

    @property
    def is_failed(self):
        """Check if the operation has failed."""
        return self.status == self.STATUS_FAILED

    @property
    def success_rate(self):
        """Calculate the success rate of the operation."""
        if self.records_processed == 0:
            return 0
        return (self.records_succeeded / self.records_processed) * 100

    def update_counters(self, succeeded=0, failed=0):
        """Update the record counters."""
        self.records_succeeded += succeeded
        self.records_failed += failed
        self.records_processed = self.records_succeeded + self.records_failed
        self.save()

    def clean(self):
        """Validate the log."""
        super().clean()
        if self.records_succeeded > self.records_processed:
            raise ValidationError({
                'records_succeeded': _('Number of successful records cannot exceed total processed records')
            })
