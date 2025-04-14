from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .base import ContactsBaseModel
from .contact import Contact

class ContactMetrics(ContactsBaseModel):
    """
    ContactMetrics model for tracking engagement and interaction metrics for contacts
    """
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    engagement_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Overall engagement score (0-100)'
    )
    last_interaction = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last interaction'
    )
    total_interactions = models.PositiveIntegerField(
        default=0,
        help_text='Total number of interactions'
    )
    email_opens = models.PositiveIntegerField(
        default=0,
        help_text='Number of email opens'
    )
    email_clicks = models.PositiveIntegerField(
        default=0,
        help_text='Number of email link clicks'
    )
    response_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text='Response rate percentage (0-100)'
    )
    average_response_time = models.DurationField(
        null=True,
        blank=True,
        help_text='Average time to respond'
    )
    communication_frequency = models.FloatField(
        default=0.0,
        help_text='Average number of communications per week'
    )

    class Meta:
        verbose_name = 'Contact Metrics'
        verbose_name_plural = 'Contact Metrics'
        indexes = [
            models.Index(fields=['contact']),
            models.Index(fields=['organization']),
            models.Index(fields=['engagement_score']),
            models.Index(fields=['last_interaction']),
        ]

    def __str__(self):
        return f"Metrics for {self.contact.name}"

    def save(self, *args, **kwargs):
        """Override save to validate metrics and update cache"""
        # Validate metrics
        if self.engagement_score < 0 or self.engagement_score > 100:
            raise ValueError("Engagement score must be between 0 and 100")
        if self.response_rate < 0 or self.response_rate > 100:
            raise ValueError("Response rate must be between 0 and 100")

        # Update last interaction if not set
        if not self.last_interaction:
            self.last_interaction = timezone.now()

        # Calculate engagement score if not set
        if not self.engagement_score:
            self.engagement_score = self.calculate_engagement_score()

        super().save(*args, **kwargs)
        
        # Update cache
        self._update_cache()

    def calculate_engagement_score(self):
        """
        Calculate overall engagement score based on various metrics
        Returns float between 0-100
        """
        weights = {
            'interaction_weight': 0.3,
            'email_engagement_weight': 0.2,
            'response_weight': 0.3,
            'frequency_weight': 0.2
        }
        
        # Normalize metrics to 0-100 scale
        interaction_score = min(self.total_interactions / 100 * 100, 100)
        email_score = ((self.email_opens + self.email_clicks * 2) / 100) * 100
        response_score = self.response_rate
        frequency_score = min(self.communication_frequency / 7 * 100, 100)
        
        # Calculate weighted score
        score = (
            interaction_score * weights['interaction_weight'] +
            email_score * weights['email_engagement_weight'] +
            response_score * weights['response_weight'] +
            frequency_score * weights['frequency_weight']
        )
        
        return round(score, 2)

    def track_interaction(self, interaction_type):
        """
        Track a new interaction
        Args:
            interaction_type (str): Type of interaction ('email_open', 'email_click', etc.)
        """
        self.total_interactions += 1
        self.last_interaction = timezone.now()
        
        if interaction_type == 'email_open':
            self.email_opens += 1
        elif interaction_type == 'email_click':
            self.email_clicks += 1
            
        self.engagement_score = self.calculate_engagement_score()
        self.save()

    def track_response_time(self, response_time):
        """
        Track response time and update average
        Args:
            response_time (timedelta): Time taken to respond
        """
        if not self.average_response_time:
            self.average_response_time = response_time
        else:
            # Calculate new average
            total_responses = self.total_interactions or 1
            current_total = self.average_response_time * (total_responses - 1)
            new_average = (current_total + response_time) / total_responses
            self.average_response_time = new_average
            
        self.save()

    def _update_cache(self):
        """Update metrics in cache"""
        cache_key = f'contact_metrics_{self.contact_id}'
        cache.set(cache_key, self, timeout=3600)  # Cache for 1 hour

    @classmethod
    def get_cached_metrics(cls, contact_id):
        """
        Get metrics from cache or database
        Args:
            contact_id (int): Contact ID
        Returns:
            ContactMetrics instance
        """
        cache_key = f'contact_metrics_{contact_id}'
        metrics = cache.get(cache_key)
        
        if not metrics:
            try:
                metrics = cls.objects.get(contact_id=contact_id)
                cache.set(cache_key, metrics, timeout=3600)
            except cls.DoesNotExist:
                return None
                
        return metrics 