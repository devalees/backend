import pytest
from django.core.exceptions import ValidationError
from Apps.contacts.models import Contact, ContactGroup
from Apps.contacts.tests.factories import ContactFactory, ContactGroupFactory

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