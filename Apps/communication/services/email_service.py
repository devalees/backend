from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from Apps.communication.models import EmailTemplate, EmailTracking, EmailAnalytics
import uuid
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        self.default_from_email = settings.DEFAULT_FROM_EMAIL
        
    def send_email(self, recipient_email, subject, message, html_message=None):
        """
        Send an email and track its status
        
        Args:
            recipient_email (str): Email address of the recipient
            subject (str): Email subject
            message (str): Email message body
            html_message (str, optional): HTML version of the message
            
        Returns:
            bool: True if email was sent successfully
            
        Raises:
            Exception: If email sending fails
        """
        tracking = None
        analytics = None
        try:
            # Create tracking record
            tracking = EmailTracking.objects.create(
                recipient_email=recipient_email,
                subject=subject,
                status='sent'
            )
            
            # Create analytics record
            analytics = EmailAnalytics.objects.create(
                email_id=str(tracking.tracking_id)
            )
            
            # Send email
            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.default_from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False
            )
            
            if not result:
                raise Exception("Failed to send email")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            if tracking:
                tracking.status = 'failed'
                tracking.save()
            raise
            
    def send_templated_email(self, template_name, recipient_email, context):
        """
        Send an email using a template
        
        Args:
            template_name (str): Name of the email template
            recipient_email (str): Email address of the recipient
            context (dict): Context variables for template rendering
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
            
            subject = template.render_subject(context)
            message = template.render_body(context)
            
            return self.send_email(recipient_email, subject, message)
            
        except EmailTemplate.DoesNotExist:
            logger.error(f"Email template {template_name} not found")
            raise
            
    def sync_emails(self):
        """
        Synchronize email status with email service provider
        
        Returns:
            bool: True if sync was successful
        """
        try:
            # TODO: Implement actual email sync logic with provider
            # This is a placeholder for the actual implementation
            return True
        except Exception as e:
            logger.error(f"Failed to sync emails: {str(e)}")
            raise
            
    def track_email_open(self, tracking_id):
        """
        Track when an email is opened
        
        Args:
            tracking_id (str): UUID of the email tracking record
        """
        try:
            tracking = EmailTracking.objects.get(tracking_id=tracking_id)
            analytics = EmailAnalytics.objects.get(email_id=str(tracking_id))
            
            tracking.status = 'opened'
            tracking.opened_at = timezone.now()
            tracking.save()
            
            analytics.increment_opens()
            
        except (EmailTracking.DoesNotExist, EmailAnalytics.DoesNotExist):
            logger.error(f"Failed to track email open for tracking_id: {tracking_id}")
            raise
            
    def track_email_click(self, tracking_id):
        """
        Track when a link in an email is clicked
        
        Args:
            tracking_id (str): UUID of the email tracking record
        """
        try:
            tracking = EmailTracking.objects.get(tracking_id=tracking_id)
            analytics = EmailAnalytics.objects.get(email_id=str(tracking_id))
            
            tracking.status = 'clicked'
            tracking.clicked_at = timezone.now()
            tracking.save()
            
            analytics.increment_clicks()
            
        except (EmailTracking.DoesNotExist, EmailAnalytics.DoesNotExist):
            logger.error(f"Failed to track email click for tracking_id: {tracking_id}")
            raise
            
    def track_email_bounce(self, tracking_id, reason):
        """
        Track when an email bounces
        
        Args:
            tracking_id (str): UUID of the email tracking record
            reason (str): Reason for the bounce
        """
        try:
            tracking = EmailTracking.objects.get(tracking_id=tracking_id)
            analytics = EmailAnalytics.objects.get(email_id=str(tracking_id))
            
            tracking.status = 'bounced'
            tracking.bounce_reason = reason
            tracking.save()
            
            analytics.increment_bounces()
            
        except (EmailTracking.DoesNotExist, EmailAnalytics.DoesNotExist):
            logger.error(f"Failed to track email bounce for tracking_id: {tracking_id}")
            raise 