from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from bs4 import BeautifulSoup
import uuid

User = get_user_model()

class Thread(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_threads', null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communication'

    def __str__(self):
        return self.title

class Message(models.Model):
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communication'

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

class Channel(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communication'

    def __str__(self):
        return self.name

class Notification(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communication'

    def __str__(self):
        return f"Notification for {self.user.username}"

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'communication'

    def __str__(self):
        return f"{self.name} ({self.code})"

class Translation(models.Model):
    source_text = models.TextField()
    target_text = models.TextField()
    source_language = models.CharField(max_length=10)
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE)
    quality_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'communication'
        indexes = [
            models.Index(fields=['source_text', 'target_language']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Translation from {self.source_language} to {self.target_language.code}: {self.source_text[:20]} -> {self.target_text[:20]}"

class Audio(models.Model):
    """Model for storing audio files."""
    file = models.FileField(upload_to='audio/')
    duration = models.FloatField(help_text="Duration in seconds")
    sample_rate = models.IntegerField(help_text="Sample rate in Hz")
    channels = models.IntegerField(help_text="Number of audio channels")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Audio {self.id} ({self.duration}s)"
    
    def get_file_size(self):
        """Return the file size in bytes."""
        return self.file.size if self.file else 0
    
    def get_content_type(self):
        """Return the content type of the audio file."""
        return 'audio/wav'  # Default to WAV, can be extended based on file extension 

class RichTextMessage(models.Model):
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'communication'

    def __str__(self):
        return f"{self.sender.username}: {self.get_preview()}"

    def clean(self):
        """Validate and sanitize HTML content."""
        soup = BeautifulSoup(self.content, 'html.parser')
        
        # Check for script tags
        if soup.find('script'):
            raise ValidationError('Script tags are not allowed')
        
        # Check for javascript: URLs in img and iframe tags
        for img in soup.find_all('img'):
            if not img.get('src'):
                raise ValidationError('Image tags must have a src attribute')
            if img['src'].lower().startswith('javascript:'):
                raise ValidationError('JavaScript URLs are not allowed in image src')
        
        for iframe in soup.find_all('iframe'):
            if not iframe.get('src'):
                raise ValidationError('Iframe tags must have a src attribute')
            if iframe['src'].lower().startswith('javascript:'):
                raise ValidationError('JavaScript URLs are not allowed in iframe src')

        # Remove disallowed attributes (style, class) from all tags
        for tag in soup.find_all(True):
            if 'style' in tag.attrs:
                del tag['style']
            if 'class' in tag.attrs:
                del tag['class']

        # Update content with sanitized HTML
        self.content = str(soup)
        super().clean()

    def save(self, *args, **kwargs):
        """Clean content before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def get_preview(self, max_length=100):
        """Get a plain text preview of the message content."""
        soup = BeautifulSoup(self.content, 'html.parser')
        # Remove colons and normalize whitespace
        text = ' '.join(soup.get_text(separator=' ', strip=True).replace(':', '').split())
        return text[:max_length] + ('...' if len(text) > max_length else '')

class EmailTemplate(models.Model):
    """Model for storing email templates"""
    name = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def render_subject(self, context):
        """Render email subject with context variables"""
        from django.template import Template, Context
        template = Template(self.subject)
        return template.render(Context(context))

    def render_body(self, context):
        """Render email body with context variables"""
        from django.template import Template, Context
        template = Template(self.body)
        return template.render(Context(context))

    def __str__(self):
        return self.name

class EmailTracking(models.Model):
    """Model for tracking email delivery and status"""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed')
    ]

    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    bounce_reason = models.TextField(null=True, blank=True)
    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"{self.recipient_email} - {self.subject}"

class EmailAnalytics(models.Model):
    """Model for tracking email analytics"""
    email_id = models.CharField(max_length=255, unique=True)
    opens = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    bounces = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def increment_opens(self):
        """Increment the number of opens"""
        self.opens += 1
        self.save()

    def increment_clicks(self):
        """Increment the number of clicks"""
        self.clicks += 1
        self.save()

    def increment_bounces(self):
        """Increment the number of bounces"""
        self.bounces += 1
        self.save()

    def __str__(self):
        return f"Analytics for {self.email_id}" 