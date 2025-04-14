from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from Apps.core.models import TaskAwareModel, TimeStampedModel
from Apps.entity.models import Organization
from ..cache_manager import ContactNoteCache
from django.conf import settings
from .contact import Contact
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class ContactNote(TimeStampedModel):
    """
    Model for storing notes related to contacts
    """
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='contact_notes'
    )
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contact_notes'
    )
    file_attachment = models.FileField(
        upload_to='contact_notes/',
        null=True,
        blank=True
    )
    file_type = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Note'
        verbose_name_plural = 'Contact Notes'

    def __str__(self):
        return f'Note for {self.contact} - {self.created_at}'

    def clean(self):
        """Validate note content and attachments"""
        if not self.content and not self.file_attachment:
            raise ValidationError("Note must have either content or an attachment")
        
        if self.file_attachment and not self.file_type:
            self.file_type = self.file_attachment.name.split('.')[-1]

    def save(self, *args, **kwargs):
        self.clean()
        
        # Handle the case where file_attachment was deleted but file_type wasn't updated
        if not self.file_attachment and self.file_type:
            self.file_type = None
        
        super().save(*args, **kwargs)

    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the note"""
        # Delete file if exists
        if self.file_attachment:
            try:
                self.file_attachment.delete(save=False)
            except Exception as e:
                logger.error(f"Error deleting file for note {self.id}: {str(e)}")
        
        # Log before deleting
        ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
        user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
        
        ContactNoteMonitoring.log_activity(
            note=None,  # Don't set note since it will be deleted
            user=user,
            activity_type='delete',
            description='Hard delete',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'method': 'hard_delete', 'note_id': self.id},
            organization=self.organization
        )
        
        # Call parent's delete method directly to bypass soft delete
        super(ContactNote, self).delete()

    def delete(self, *args, **kwargs):
        """Delete the note"""
        hard_delete = kwargs.pop('hard_delete', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        if hard_delete:
            return self.hard_delete(user=user, request_meta=request_meta)
            
        # Soft delete
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()


class ContactNoteMonitoring(models.Model):
    """ContactNoteMonitoring model for tracking interactions with notes"""
    
    ACTIVITY_TYPES = (
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('attachment_add', 'Add Attachment'),
        ('attachment_remove', 'Remove Attachment'),
        ('other', 'Other')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.ForeignKey(
        ContactNote,
        on_delete=models.CASCADE,
        related_name='monitoring_records',
        null=True,  # Allow recording events for deleted notes
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Allow system-generated events
        related_name='note_activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES,
    )
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        'entity.Organization',
        on_delete=models.CASCADE,
        related_name='note_monitoring_records'
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _('Note Activity Record')
        verbose_name_plural = _('Note Activity Records')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['note', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.activity_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def log_activity(cls, note=None, user=None, activity_type=None, description=None, 
                    ip_address=None, user_agent=None, metadata=None, organization=None):
        """Log an activity related to a note"""
        if not organization and note:
            organization = note.organization
            
        if not metadata:
            metadata = {}
            
        record = cls.objects.create(
            note=note,
            user=user,
            activity_type=activity_type,
            description=description,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata
        )
        return record


class ContactNoteNotification(models.Model):
    """ContactNoteNotification model for managing note-related notifications"""
    
    NOTIFICATION_TYPES = (
        ('mention', 'Mention'),
        ('comment', 'Comment'),
        ('attachment', 'Attachment'),
        ('other', 'Other')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.ForeignKey(
        ContactNote,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='note_notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _('Note Notification')
        verbose_name_plural = _('Note Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['note', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_read(self):
        """Mark the notification as read"""
        self.is_read = True
        self.save() 