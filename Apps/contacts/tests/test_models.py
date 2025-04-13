import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db.utils import IntegrityError
from Apps.contacts.models import Contact, ContactGroup, ContactTemplate, ContactMonitoring
from Apps.contacts.tests.factories import ContactFactory, ContactGroupFactory, ContactTemplateFactory
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization
from django.db import transaction

User = get_user_model()

@pytest.mark.django_db
class TestContact:
    def test_create_contact(self):
        """Test creating a contact"""
        contact = ContactFactory()
        assert contact.name is not None
        assert contact.email is not None
        assert contact.phone is not None
        assert contact.organization is not None
        assert contact.department is not None
        assert contact.team is not None
        assert contact.created_by is not None
        assert contact.is_active

    def test_contact_str(self):
        """Test string representation of contact"""
        contact = ContactFactory()
        assert str(contact) == contact.name

    def test_contact_soft_delete(self):
        """Test soft delete functionality"""
        contact = ContactFactory()
        contact.delete()
        assert not contact.is_active
        assert Contact.objects.filter(id=contact.id).exists()

    def test_contact_hard_delete(self):
        """Test hard delete functionality"""
        contact = ContactFactory()
        contact.hard_delete()
        assert not Contact.objects.filter(id=contact.id).exists()

    def test_unique_email_constraint(self):
        """Test that email must be unique"""
        contact = ContactFactory()
        with pytest.raises(ValidationError):
            ContactFactory(email=contact.email)

    def test_contact_validation(self):
        """Test contact validation"""
        # Test invalid email
        with pytest.raises(ValidationError):
            contact = ContactFactory(email="invalid-email")
            contact.full_clean()

        # Test invalid phone
        with pytest.raises(ValidationError):
            contact = ContactFactory(phone="invalid-phone")
            contact.full_clean()

@pytest.mark.django_db
class TestContactGroup:
    def test_create_contact_group(self):
        """Test creating a contact group"""
        group = ContactGroupFactory()
        assert group.name is not None
        assert group.description is not None
        assert group.organization is not None
        assert group.created_by is not None
        assert group.is_active

    def test_contact_group_str(self):
        """Test string representation of contact group"""
        group = ContactGroupFactory()
        assert str(group) == group.name

    def test_contact_group_soft_delete(self):
        """Test soft delete functionality"""
        group = ContactGroupFactory()
        group.delete()
        assert not group.is_active
        assert ContactGroup.objects.filter(id=group.id).exists()

    def test_contact_group_hard_delete(self):
        """Test hard delete functionality"""
        group = ContactGroupFactory()
        group.hard_delete()
        assert not ContactGroup.objects.filter(id=group.id).exists()

    def test_add_contact_to_group(self):
        """Test adding a contact to a group"""
        group = ContactGroupFactory()
        contact = ContactFactory()
        group.contacts.add(contact)
        assert contact in group.contacts.all()
        assert group in contact.groups.all()

    def test_remove_contact_from_group(self):
        """Test removing a contact from a group"""
        group = ContactGroupFactory()
        contact = ContactFactory()
        group.contacts.add(contact)
        group.contacts.remove(contact)
        assert contact not in group.contacts.all()
        assert group not in contact.groups.all()

@pytest.mark.django_db
class TestContactTemplate:
    """Test cases for ContactTemplate model"""
    
    def test_create_contact_template(self):
        """Test creating a contact template"""
        template = ContactTemplateFactory()
        
        assert template.name is not None
        assert template.description is not None
        assert template.organization is not None
        assert template.created_by is not None
        assert template.updated_by is not None
        assert template.fields is not None
        assert template.is_active
        
    def test_template_str(self):
        """Test string representation of template"""
        template = ContactTemplateFactory(name="Test Template")
        assert str(template) == "Test Template"
        
    def test_template_soft_delete(self):
        """Test soft delete functionality"""
        template = ContactTemplateFactory()
        template.delete()
        assert not template.is_active
        assert ContactTemplate.objects.filter(id=template.id).exists()
        
    def test_template_hard_delete(self):
        """Test hard delete functionality"""
        template = ContactTemplateFactory()
        template.hard_delete()
        assert not ContactTemplate.objects.filter(id=template.id).exists()
        
    def test_template_fields_validation(self):
        """Test fields validation in more detail"""
        # Test with valid fields
        template = ContactTemplateFactory()
        template.full_clean()  # Should not raise
        
        # Test with invalid fields (not a dict)
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields = "not a dict"
            template.full_clean()
        
        # Test with invalid field type
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields['name']['type'] = 'invalid_type'
            template.full_clean()
            
        # Test with missing required property
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            del template.fields['name']['required']
            template.full_clean()
            
        # Test with non-boolean required
        with pytest.raises(ValidationError):
            template = ContactTemplateFactory()
            template.fields['name']['required'] = "not a boolean"
            template.full_clean()
            
    def test_unique_organization_constraint(self):
        """Test unique constraint for name within organization"""
        # Create a template
        template1 = ContactTemplateFactory(name="Unique Template")
    
        # Try to create another with same name and org
        with pytest.raises(ValidationError):
            template2 = ContactTemplateFactory.build(
                name="Unique Template",
                organization=template1.organization
            )
            # Use full_clean() to trigger validation before database insert
            template2.full_clean() 