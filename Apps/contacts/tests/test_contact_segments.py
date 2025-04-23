import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from Apps.contacts.models import ContactSegment, ContactList, Contact
from Apps.contacts.tests.factories import ContactFactory, ContactListFactory, OrganizationFactory, UserFactory, ContactSegmentFactory
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization
from django.db import transaction

User = get_user_model()

@pytest.mark.django_db
class TestContactSegment:
    """Test suite for ContactSegment model"""
    
    def test_create_contact_segment(self):
        """Test creating a contact segment"""
        contact_list = ContactListFactory()
        segment = ContactSegmentFactory(contact_list=contact_list)
        
        assert segment.name is not None
        assert segment.description is not None
        assert segment.contact_list is not None
        assert segment.created_by is not None
        assert segment.is_active
        assert segment.filter_criteria is not None
        assert isinstance(segment.filter_criteria, dict)
    
    def test_contact_segment_str(self):
        """Test string representation of contact segment"""
        segment = ContactSegmentFactory()
        assert str(segment) == segment.name
    
    def test_contact_segment_soft_delete(self):
        """Test soft delete functionality"""
        segment = ContactSegmentFactory()
        segment.delete()
        assert not segment.is_active
        assert ContactSegment.objects.filter(id=segment.id).exists()
    
    def test_contact_segment_hard_delete(self):
        """Test hard delete functionality"""
        segment = ContactSegmentFactory()
        segment.hard_delete()
        assert not ContactSegment.objects.filter(id=segment.id).exists()
    
    def test_segment_validation(self):
        """Test segment validation"""
        org = OrganizationFactory()
        contact_list = ContactListFactory(organization=org)
        
        # Test valid segment
        segment = ContactSegment(
            name="Valid Segment",
            description="A valid segment",
            contact_list=contact_list,
            created_by=UserFactory(),
            filter_criteria={"field": "email", "operator": "contains", "value": "example.com"}
        )
        segment.full_clean()
        
        # Test invalid filter criteria
        with pytest.raises(ValidationError) as excinfo:
            segment = ContactSegment(
                name="Invalid Segment",
                description="An invalid segment",
                contact_list=contact_list,
                created_by=UserFactory(),
                filter_criteria={"invalid": "criteria"}
            )
            segment.full_clean()
        
        assert "filter_criteria" in str(excinfo.value)
    
    def test_unique_name_constraint(self):
        """Test unique name constraint within a contact list"""
        contact_list = ContactListFactory()
        
        # Create first segment
        segment1 = ContactSegmentFactory(
            name="Test Segment",
            contact_list=contact_list
        )
        
        # Try to create another segment with the same name in the same list
        with pytest.raises(ValidationError):
            segment2 = ContactSegment(
                name="Test Segment",
                contact_list=contact_list,
                created_by=UserFactory(),
                filter_criteria={"field": "email", "operator": "contains", "value": "example.com"}
            )
            segment2.full_clean()  # This should raise ValidationError for unique_together constraint
        
        # Should be able to create a segment with the same name in a different list
        other_list = ContactListFactory()
        segment3 = ContactSegmentFactory(
            name="Test Segment",
            contact_list=other_list
        )
        assert segment3.name == "Test Segment"
    
    def test_apply_filter_criteria(self):
        """Test applying filter criteria to get matching contacts"""
        contact_list = ContactListFactory()
        
        # Create test contacts with different email domains
        ContactFactory(contact_list=contact_list, email="test1@example.com")
        ContactFactory(contact_list=contact_list, email="test2@example.com")
        ContactFactory(contact_list=contact_list, email="test3@other.com")
        
        # Create segment with filter for example.com domain
        segment = ContactSegmentFactory(
            contact_list=contact_list,
            filter_criteria={
                "field": "email",
                "operator": "contains",
                "value": "example.com"
            }
        )
        
        # Get matching contacts
        matching_contacts = segment.get_matching_contacts()
        
        # ContactListFactory creates 3 contacts by default and we added 2 more with example.com
        # Total matching should be 5 contacts with example.com in their email
        assert matching_contacts.count() == 5
        # Check that all contacts have example.com in their email
        for contact in matching_contacts:
            assert "example.com" in contact.email.lower()
    
    def test_complex_filter_criteria(self):
        """Test applying complex filter criteria with AND/OR operators"""
        contact_list = ContactListFactory()
        
        # Create test contacts with different attributes
        contact1 = ContactFactory(contact_list=contact_list, email="test1@example.com", first_name="John")
        contact2 = ContactFactory(contact_list=contact_list, email="test2@example.com", first_name="Jane")
        contact3 = ContactFactory(contact_list=contact_list, email="test3@other.com", first_name="John")
        
        # Create segment with complex filter criteria
        segment = ContactSegmentFactory(
            contact_list=contact_list,
            filter_criteria={
                "operator": "and",
                "criteria": [
                    {
                        "field": "email",
                        "operator": "contains",
                        "value": "example.com"
                    },
                    {
                        "field": "first_name",
                        "operator": "equals",
                        "value": "John"
                    }
                ]
            }
        )
        
        # Get matching contacts
        matching_contacts = segment.get_matching_contacts()
        
        # Should find only contact1 matching both criteria
        assert matching_contacts.filter(id=contact1.id).exists()
        assert not matching_contacts.filter(id=contact2.id).exists()  # Doesn't match first_name
        assert not matching_contacts.filter(id=contact3.id).exists()  # Doesn't match email
    
    def test_update_segment(self):
        """Test updating a segment"""
        segment = ContactSegmentFactory()
        
        # Update segment
        segment.name = "Updated Segment"
        segment.description = "Updated description"
        segment.filter_criteria = {"field": "name", "operator": "contains", "value": "Updated"}
        segment.save()
        
        # Retrieve from database
        updated_segment = ContactSegment.objects.get(id=segment.id)
        
        # Check updates
        assert updated_segment.name == "Updated Segment"
        assert updated_segment.description == "Updated description"
        assert updated_segment.filter_criteria == {"field": "name", "operator": "contains", "value": "Updated"}
    
    def test_metadata_field(self):
        """Test metadata field functionality"""
        segment = ContactSegmentFactory()
        
        # Set metadata
        segment.metadata = {
            "last_run": "2023-01-01",
            "contact_count": 10,
            "is_dynamic": True
        }
        segment.save()
        
        # Retrieve from database
        updated_segment = ContactSegment.objects.get(id=segment.id)
        
        # Check metadata
        assert updated_segment.metadata["last_run"] == "2023-01-01"
        assert updated_segment.metadata["contact_count"] == 10
        assert updated_segment.metadata["is_dynamic"] is True
    
    def test_get_active_segments(self):
        """Test getting active segments"""
        contact_list = ContactListFactory()
        
        # Create active and inactive segments
        active_segment1 = ContactSegmentFactory(contact_list=contact_list, is_active=True)
        active_segment2 = ContactSegmentFactory(contact_list=contact_list, is_active=True)
        inactive_segment = ContactSegmentFactory(contact_list=contact_list, is_active=False)
        
        # Get active segments
        active_segments = ContactSegment.objects.filter(is_active=True)
        
        # Should have 2 active segments
        assert len(active_segments) == 2
        assert active_segment1 in active_segments
        assert active_segment2 in active_segments
        assert inactive_segment not in active_segments 