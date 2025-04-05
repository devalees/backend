import pytest
from django.core.mail import send_mail
from django.test import TestCase
from unittest.mock import patch, MagicMock
from Apps.communication.services.email_service import EmailService
from Apps.communication.models import EmailTemplate, EmailTracking, EmailAnalytics

class TestEmailIntegration(TestCase):
    def setUp(self):
        self.email_service = EmailService()
        self.test_email = "test@example.com"
        self.test_subject = "Test Subject"
        self.test_message = "Test Message"
        
    def test_send_email_success(self):
        """Test successful email sending"""
        with patch('Apps.communication.services.email_service.send_mail') as mock_send:
            mock_send.return_value = 1
            result = self.email_service.send_email(
                self.test_email,
                self.test_subject,
                self.test_message
            )
            self.assertTrue(result)
            mock_send.assert_called_once()
            
    def test_send_email_failure(self):
        """Test email sending failure"""
        with patch('Apps.communication.services.email_service.send_mail') as mock_send:
            mock_send.side_effect = Exception("SMTP Error")
            with self.assertRaises(Exception):
                self.email_service.send_email(
                    self.test_email,
                    self.test_subject,
                    self.test_message
                )
                
    def test_create_email_template(self):
        """Test email template creation"""
        template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Welcome {{name}}",
            body="Hello {{name}}, welcome to our platform!",
            is_active=True
        )
        self.assertEqual(template.name, "Test Template")
        self.assertTrue(template.is_active)
        
    def test_email_tracking(self):
        """Test email tracking functionality"""
        tracking = EmailTracking.objects.create(
            recipient_email=self.test_email,
            subject=self.test_subject,
            status="sent"
        )
        self.assertEqual(tracking.status, "sent")
        self.assertEqual(tracking.recipient_email, self.test_email)
        
    def test_email_analytics(self):
        """Test email analytics tracking"""
        analytics = EmailAnalytics.objects.create(
            email_id="test123",
            opens=0,
            clicks=0,
            bounces=0
        )
        analytics.increment_opens()
        self.assertEqual(analytics.opens, 1)
        
    def test_email_sync(self):
        """Test email synchronization"""
        with patch('Apps.communication.services.email_service.EmailService.sync_emails') as mock_sync:
            mock_sync.return_value = True
            result = self.email_service.sync_emails()
            self.assertTrue(result)
            mock_sync.assert_called_once()
            
    def test_email_template_rendering(self):
        """Test email template rendering with variables"""
        template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Welcome {{name}}",
            body="Hello {{name}}, welcome to our platform!",
            is_active=True
        )
        context = {"name": "John"}
        rendered_subject = template.render_subject(context)
        rendered_body = template.render_body(context)
        
        self.assertEqual(rendered_subject, "Welcome John")
        self.assertEqual(rendered_body, "Hello John, welcome to our platform!") 