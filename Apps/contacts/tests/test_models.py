import pytest
from django.core.exceptions import ValidationError
from Apps.contacts.models import Contact, ContactGroup, ContactTemplate
from Apps.contacts.tests.factories import ContactFactory, ContactGroupFactory
from django.test import TestCase
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization

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

class ContactTemplateTests(TestCase):
    """Test cases for ContactTemplate model"""
    
    def setUp(self):
        """Set up test data"""
        self.organization = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.template_data = {
            'name': 'Standard Contact Template',
            'description': 'A standard template for contacts',
            'organization': self.organization,
            'created_by': self.user,
            'fields': {
                'name': {'required': True, 'type': 'text'},
                'email': {'required': True, 'type': 'email'},
                'phone': {'required': True, 'type': 'phone'},
                'department': {'required': False, 'type': 'select'},
                'team': {'required': False, 'type': 'select'}
            }
        }

    def test_create_contact_template(self):
        """Test creating a contact template"""
        template = ContactTemplate.objects.create(**self.template_data)
        self.assertEqual(template.name, self.template_data['name'])
        self.assertEqual(template.organization, self.organization)
        self.assertEqual(template.created_by, self.user)
        self.assertEqual(template.fields, self.template_data['fields'])

    def test_template_validation(self):
        """Test template validation"""
        # Test required fields
        with self.assertRaises(ValidationError):
            ContactTemplate.objects.create(
                organization=self.organization,
                created_by=self.user
            )

        # Test invalid fields structure
        invalid_data = self.template_data.copy()
        invalid_data['fields'] = 'invalid'
        with self.assertRaises(ValidationError):
            ContactTemplate.objects.create(**invalid_data)

    def test_template_str_representation(self):
        """Test string representation of template"""
        template = ContactTemplate.objects.create(**self.template_data)
        self.assertEqual(str(template), self.template_data['name'])

    def test_template_soft_delete(self):
        """Test soft delete functionality"""
        template = ContactTemplate.objects.create(**self.template_data)
        template.delete()
        self.assertFalse(template.is_active)
        self.assertTrue(ContactTemplate.objects.filter(id=template.id).exists())

    def test_template_hard_delete(self):
        """Test hard delete functionality"""
        template = ContactTemplate.objects.create(**self.template_data)
        template.hard_delete()
        self.assertFalse(ContactTemplate.objects.filter(id=template.id).exists())

    def test_template_organization_constraint(self):
        """Test organization constraint"""
        other_org = Organization.objects.create(name="Other Org")
        template = ContactTemplate.objects.create(**self.template_data)
        
        # Try to change organization
        template.organization = other_org
        with self.assertRaises(ValidationError):
            template.save()

    def test_template_fields_validation(self):
        """Test fields validation"""
        # Test missing required field type
        invalid_fields = self.template_data['fields'].copy()
        del invalid_fields['name']['type']
        invalid_data = self.template_data.copy()
        invalid_data['fields'] = invalid_fields
        with self.assertRaises(ValidationError):
            ContactTemplate.objects.create(**invalid_data)

        # Test invalid field type
        invalid_fields = self.template_data['fields'].copy()
        invalid_fields['name']['type'] = 'invalid_type'
        invalid_data = self.template_data.copy()
        invalid_data['fields'] = invalid_fields
        with self.assertRaises(ValidationError):
            ContactTemplate.objects.create(**invalid_data) 