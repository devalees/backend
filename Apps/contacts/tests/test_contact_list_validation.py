import pytest
from django.core.exceptions import ValidationError
from Apps.contacts.models import ContactList, Contact
from Apps.contacts.tests.factories import ContactFactory, ContactListFactory, OrganizationFactory, UserFactory
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestContactListValidation:
    """Test suite for ContactList validation"""
    
    def test_validate_name_required(self):
        """Test that name is required"""
        org = OrganizationFactory()
        with pytest.raises(ValidationError) as excinfo:
            contact_list = ContactList(
                name="", 
                organization=org,
                created_by=UserFactory()
            )
            contact_list.full_clean()
        
        assert "name" in str(excinfo.value)
    
    def test_validate_name_max_length(self):
        """Test that name has a maximum length"""
        org = OrganizationFactory()
        long_name = "a" * 256  # Exceeds max_length of 255
        
        with pytest.raises(ValidationError) as excinfo:
            contact_list = ContactList(
                name=long_name, 
                organization=org,
                created_by=UserFactory()
            )
            contact_list.full_clean()
        
        assert "name" in str(excinfo.value)
    
    def test_validate_organization_required(self):
        """Test that organization is required"""
        with pytest.raises(ValidationError) as excinfo:
            contact_list = ContactList(
                name="Test List",
                created_by=UserFactory()
            )
            contact_list.full_clean()
        
        assert "organization" in str(excinfo.value)
    
    def test_validate_unique_name_per_organization(self):
        """Test that name must be unique within an organization"""
        org = OrganizationFactory()
        ContactListFactory(name="Test List", organization=org)
        
        with pytest.raises(ValidationError) as excinfo:
            contact_list = ContactList(
                name="Test List", 
                organization=org,
                created_by=UserFactory()
            )
            contact_list.full_clean()
        
        assert "name" in str(excinfo.value)
    
    def test_validate_contacts_from_same_organization(self):
        """Test that all contacts must belong to the same organization as the list"""
        org = OrganizationFactory()
        other_org = OrganizationFactory()
        
        contact_list = ContactListFactory(organization=org)
        valid_contact = ContactFactory(organization=org)
        invalid_contact = ContactFactory(organization=other_org)
        
        # Add both contacts to the list
        contact_list.contacts.add(valid_contact, invalid_contact)
        
        # Validation should fail because of the invalid contact
        with pytest.raises(ValidationError) as excinfo:
            contact_list.clean()
        
        assert "contacts" in str(excinfo.value)
    
    def test_validate_contacts_all_valid(self):
        """Test that validation passes when all contacts belong to the same organization"""
        org = OrganizationFactory()
        contact_list = ContactListFactory(organization=org)
        
        # Create multiple contacts from the same organization
        contacts = ContactFactory.create_batch(3, organization=org)
        
        # Add all contacts to the list
        contact_list.contacts.add(*contacts)
        
        # Validation should pass
        contact_list.clean()
    
    def test_validate_metadata_format(self):
        """Test that metadata must be a valid JSON object"""
        org = OrganizationFactory()
        contact_list = ContactListFactory(organization=org)
        
        # Set invalid metadata (not a dict)
        contact_list.metadata = "invalid metadata"
        
        with pytest.raises(ValidationError) as excinfo:
            contact_list.clean()
        
        assert "metadata" in str(excinfo.value)
    
    def test_validate_metadata_valid(self):
        """Test that valid metadata passes validation"""
        org = OrganizationFactory()
        contact_list = ContactListFactory(organization=org)
        
        # Set valid metadata
        contact_list.metadata = {
            "category": "VIP",
            "source": "Import",
            "tags": ["important", "follow-up"]
        }
        
        # Validation should pass
        contact_list.clean()
    
    def test_validate_description_optional(self):
        """Test that description is optional"""
        org = OrganizationFactory()
        contact_list = ContactList(
            name="Test List", 
            organization=org,
            created_by=UserFactory(),
            description=None
        )
        
        # Validation should pass
        contact_list.clean()
    
    def test_validate_description_max_length(self):
        """Test that description has a reasonable length"""
        org = OrganizationFactory()
        contact_list = ContactList(
            name="Test List", 
            organization=org,
            created_by=UserFactory(),
            description="a" * 10001  # Very long description
        )
        
        # Validation should pass as TextField has no max_length
        contact_list.clean() 