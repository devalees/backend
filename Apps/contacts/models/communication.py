from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .base import ContactsBaseModel, Organization
from .contact import Contact
from ..cache_manager import CommunicationCache

class Communication(ContactsBaseModel):
    """Communication model for tracking messages sent to contacts"""
    
    COMMUNICATION_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('call', 'Call'),
        ('letter', 'Letter'),
        ('meeting', 'Meeting'),
        ('other', 'Other')
    )
    
    STATUS_TYPES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    )
    
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='communications'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='communications'
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    communication_type = models.CharField(
        max_length=20,
        choices=COMMUNICATION_TYPES,
        default='email'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_TYPES,
        default='draft'
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Communication'
        verbose_name_plural = 'Communications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact']),
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
            models.Index(fields=['communication_type']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return self.subject
    
    @property
    def is_sent(self):
        """Return True if the communication has been sent"""
        return self.status == 'sent'
    
    @property
    def is_failed(self):
        """Return True if the communication has failed"""
        return self.status == 'failed'
    
    def save(self, *args, **kwargs):
        """Save the communication and validate data"""
        skip_validation = kwargs.pop('skip_validation', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        
        # Determine if this is a create or update
        is_create = self._state.adding
        
        if not skip_validation:
            self.full_clean()
            
        # If status is transitioning to 'sent', update sent_at
        if self.status == 'sent' and (is_create or not Communication.objects.get(pk=self.pk).is_sent):
            self.sent_at = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Cache the communication
        CommunicationCache.set_communication(self, include_related=True)
        
        # Log the activity
        if hasattr(self, '__class__') and hasattr(self.__class__, 'objects'):
            activity_type = 'create' if is_create else 'update'
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT')
            
            from .monitoring import CommunicationMonitoring
            CommunicationMonitoring.log_activity(
                communication=self,
                user=user,
                activity_type=activity_type,
                description=f"{'Created' if is_create else 'Updated'} via model save",
                ip_address=ip_address,
                user_agent=user_agent
            )
    
    def hard_delete(self, user=None, request_meta=None):
        """Hard delete the communication"""
        self.delete(hard_delete=True, user=user, request_meta=request_meta)
    
    def delete(self, *args, **kwargs):
        """Delete the communication"""
        hard_delete = kwargs.pop('hard_delete', False)
        user = kwargs.pop('user', None)
        request_meta = kwargs.pop('request_meta', {})
        org_id = self.organization_id
        org = self.organization
        
        if hard_delete:
            # Log before deleting
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                
                from .monitoring import CommunicationMonitoring
                CommunicationMonitoring.log_activity(
                    communication=None,  # Don't set communication since it will be deleted
                    user=user,
                    activity_type='delete',
                    description='Hard delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'hard_delete', 'communication_id': self.id},
                    organization=org  # Explicitly set organization
                )
                
            # Call the parent class's delete method
            super().delete(*args, **kwargs)
            
            # Clear cache
            CommunicationCache.delete_communication(self.id, org_id, force_delete=True)
        else:
            # Soft delete - set is_active to False
            self.is_active = False
            self.save(skip_validation=True)
            
            # Log the soft delete activity
            if org:
                ip_address = request_meta.get('REMOTE_ADDR') if request_meta else None
                user_agent = request_meta.get('HTTP_USER_AGENT') if request_meta else None
                
                from .monitoring import CommunicationMonitoring
                CommunicationMonitoring.log_activity(
                    communication=self,
                    user=user,
                    activity_type='delete',
                    description='Soft delete',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'method': 'soft_delete', 'communication_id': self.id},
                    organization=org
                )
    
    def clean(self):
        """Validate communication data"""
        # Validate communication type
        valid_types = dict(self.COMMUNICATION_TYPES).keys()
        if self.communication_type not in valid_types:
            raise ValidationError({'communication_type': [f'Invalid communication type. Must be one of {valid_types}']})
        
        # Validate status
        valid_statuses = dict(self.STATUS_TYPES).keys()
        if self.status not in valid_statuses:
            raise ValidationError({'status': [f'Invalid status. Must be one of {valid_statuses}']})
        
        # Validate scheduled communication
        if self.status == 'scheduled' and not self.scheduled_at:
            raise ValidationError({'scheduled_at': ['Scheduled communications must have a scheduled date and time.']})
        
        # Check if contact belongs to the organization
        if self.contact and self.contact.organization != self.organization:
            raise ValidationError({'contact': ['Contact must belong to the communication\'s organization.']})

@receiver(post_save, sender=Communication)
def communication_post_save(sender, instance, created, **kwargs):
    """Update cache when communication is saved"""
    CommunicationCache.set_communication(instance, include_related=True)
    CommunicationCache.invalidate_contact_communications(instance.contact_id)
    CommunicationCache.invalidate_organization_communications(instance.organization_id)

@receiver(post_delete, sender=Communication)
def communication_post_delete(sender, instance, **kwargs):
    """Update cache when communication is deleted"""
    CommunicationCache.delete_communication(instance.id, instance.organization_id)

class CommunicationTemplate(ContactsBaseModel):
    """CommunicationTemplate model for defining message templates"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='communication_templates'
    )
    subject_template = models.CharField(max_length=255)
    message_template = models.TextField()
    communication_type = models.CharField(
        max_length=20,
        choices=Communication.COMMUNICATION_TYPES,
        default='email'
    )
    
    class Meta:
        verbose_name = 'Communication Template'
        verbose_name_plural = 'Communication Templates'
        ordering = ['name']
        unique_together = ['name', 'organization']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Save the template"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def hard_delete(self):
        """Hard delete the template"""
        super().delete()
        
    def delete(self, *args, **kwargs):
        """Soft delete the template"""
        self.is_active = False
        self.save()
        
    def clean(self):
        """Validate template"""
        # Validate communication type
        valid_types = dict(Communication.COMMUNICATION_TYPES).keys()
        if self.communication_type not in valid_types:
            raise ValidationError({'communication_type': [f'Invalid communication type. Must be one of {valid_types}']})
    
    def create_communication(self, contact, user=None):
        """Create a communication based on this template"""
        # Validate contact belongs to same organization
        if contact.organization != self.organization:
            raise ValidationError('Contact must belong to the same organization as the template')
        
        # Simple template rendering using string replacement
        # In a real app, you might use a more robust template engine
        context = {'contact': contact}
        
        # Render subject and message
        subject = self._render_template(self.subject_template, context)
        message = self._render_template(self.message_template, context)
        
        # Create communication
        communication = Communication.objects.create(
            contact=contact,
            organization=self.organization,
            subject=subject,
            message=message,
            communication_type=self.communication_type,
            status='draft',
            created_by=user,
            updated_by=user
        )
        
        return communication
    
    def _render_template(self, template_string, context):
        """Render template with context data"""
        # Replace {{var}} placeholders
        # This is a simple implementation - a real app would use a proper template engine
        result = template_string
        
        # Handle {{contact.attribute}} replacements
        if 'contact' in context:
            contact = context['contact']
            for field in ['name', 'email', 'phone']:
                placeholder = f'{{{{contact.{field}}}}}'
                value = getattr(contact, field, '')
                result = result.replace(placeholder, str(value))
        
        return result
