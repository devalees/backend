import pytest
from django.utils import timezone
from datetime import timedelta
from Apps.contacts.models import Contact, ContactMetrics
from Apps.contacts.tests.factories import ContactFactory
from Apps.core.tests.factories import UserFactory
from Apps.entity.tests.factories import OrganizationFactory

@pytest.mark.django_db
class TestContactMetrics:
    """Test cases for ContactMetrics model"""
    
    def test_create_metrics(self):
        """Test creating contact metrics"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization,
            engagement_score=75.5,
            last_interaction=timezone.now(),
            total_interactions=10,
            email_opens=5,
            email_clicks=3,
            response_rate=60.0,
            average_response_time=timedelta(hours=2),
            communication_frequency=7.5
        )
        
        assert metrics.id is not None
        assert metrics.contact == contact
        assert metrics.organization == contact.organization
        assert metrics.engagement_score == 75.5
        assert metrics.total_interactions == 10
        assert metrics.email_opens == 5
        assert metrics.email_clicks == 3
        assert metrics.response_rate == 60.0
        assert metrics.average_response_time == timedelta(hours=2)
        assert metrics.communication_frequency == 7.5

    def test_update_metrics(self):
        """Test updating contact metrics"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization,
            engagement_score=50.0,
            total_interactions=5
        )
        
        # Update metrics
        metrics.engagement_score = 75.0
        metrics.total_interactions = 10
        metrics.save()
        
        # Refresh from database
        metrics.refresh_from_db()
        assert metrics.engagement_score == 75.0
        assert metrics.total_interactions == 10

    def test_calculate_engagement_score(self):
        """Test calculating engagement score"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization,
            total_interactions=20,
            email_opens=10,
            email_clicks=5,
            response_rate=80.0,
            communication_frequency=5.0
        )
        
        score = metrics.calculate_engagement_score()
        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_track_interaction(self):
        """Test tracking a new interaction"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization,
            total_interactions=5
        )
        
        metrics.track_interaction('email_open')
        assert metrics.total_interactions == 6
        assert metrics.email_opens == 1

    def test_track_response_time(self):
        """Test tracking response time"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization
        )
        
        # Simulate response after 2 hours
        response_time = timedelta(hours=2)
        metrics.track_response_time(response_time)
        
        assert metrics.average_response_time is not None
        assert metrics.average_response_time == response_time

    def test_metrics_validation(self):
        """Test metrics validation"""
        contact = ContactFactory()
        
        with pytest.raises(ValueError):
            ContactMetrics.objects.create(
                contact=contact,
                organization=contact.organization,
                engagement_score=150.0  # Invalid score > 100
            )
            
        with pytest.raises(ValueError):
            ContactMetrics.objects.create(
                contact=contact,
                organization=contact.organization,
                response_rate=120.0  # Invalid rate > 100
            )

    def test_metrics_caching(self):
        """Test metrics caching"""
        contact = ContactFactory()
        metrics = ContactMetrics.objects.create(
            contact=contact,
            organization=contact.organization,
            engagement_score=75.0
        )
        
        # Test cache hit
        cached_metrics = ContactMetrics.get_cached_metrics(contact.id)
        assert cached_metrics is not None
        assert cached_metrics.engagement_score == 75.0

        # Test cache invalidation
        metrics.engagement_score = 80.0
        metrics.save()
        
        updated_metrics = ContactMetrics.get_cached_metrics(contact.id)
        assert updated_metrics.engagement_score == 80.0 