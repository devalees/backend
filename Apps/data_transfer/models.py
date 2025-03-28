from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class DataTransferModel(models.Model):
    """
    Model to track data transfer operations and their status
    """
    TRANSFER_TYPE_CHOICES = [
        ('import', _('Import')),
        ('export', _('Export')),
    ]
    
    FILE_TYPE_CHOICES = [
        ('csv', _('CSV')),
        ('excel', _('Excel')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    name = models.CharField(_('Operation Name'), max_length=255)
    transfer_type = models.CharField(_('Transfer Type'), max_length=10, choices=TRANSFER_TYPE_CHOICES)
    file_type = models.CharField(_('File Type'), max_length=10, choices=FILE_TYPE_CHOICES)
    source_model = models.CharField(_('Source Model'), max_length=255)
    file_path = models.FileField(_('File Path'), upload_to='data_transfers/')
    field_mapping = models.JSONField(_('Field Mapping'), null=True, blank=True)
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(_('Error Message'), null=True, blank=True)
    records_processed = models.IntegerField(_('Records Processed'), default=0)
    records_failed = models.IntegerField(_('Records Failed'), default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_data_transfers')
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    class Meta:
        verbose_name = _('Data Transfer')
        verbose_name_plural = _('Data Transfers')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.transfer_type} ({self.status})"

    def mark_as_processing(self):
        """Mark the transfer as processing"""
        self.status = 'processing'
        self.save()

    def mark_as_completed(self, records_processed):
        """Mark the transfer as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.records_processed = records_processed
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message):
        """Mark the transfer as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    @property
    def duration(self):
        """Calculate the duration of the transfer operation"""
        if self.completed_at and self.created_at:
            return self.completed_at - self.created_at
        return None

# Keep TestModel for testing purposes
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    age = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_test_models')

    def __str__(self):
        return self.name
