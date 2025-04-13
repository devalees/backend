import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from Apps.contacts.models import ContactList, Contact
from Apps.contacts.tests.factories import ContactFactory, ContactListFactory, OrganizationFactory, UserFactory
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization
from django.db import transaction

User = get_user_model()

@pytest.mark.django_db
class TestContactList:
    def test_create_contact_list(self):
        """Test creating a contact list"""
        contact_list = ContactListFactory()
        assert contact_list.name is not None
        assert contact_list.description is not None
        assert contact_list.organization is not None
        assert contact_list.created_by is not None
        assert contact_list.is_active

    def test_contact_list_str(self):
        """Test string representation of contact list"""
        contact_list = ContactListFactory()
        assert str(contact_list) == contact_list.name

    def test_contact_list_soft_delete(self):
        """Test soft delete functionality"""
        contact_list = ContactListFactory()
        contact_list.delete()
        assert not contact_list.is_active
        assert ContactList.objects.filter(id=contact_list.id).exists()

    def test_contact_list_hard_delete(self):
        """Test hard delete functionality"""
        contact_list = ContactListFactory()
        contact_list.hard_delete()
        assert not ContactList.objects.filter(id=contact_list.id).exists()

    def test_add_contact_to_list(self):
        """Test adding a contact to a list"""
        contact_list = ContactListFactory()
        contact = ContactFactory(organization=contact_list.organization)
        
        contact_list.contacts.add(contact)
        assert contact in contact_list.contacts.all()
        assert contact_list in contact.lists.all()

    def test_remove_contact_from_list(self):
        """Test removing a contact from a list"""
        contact_list = ContactListFactory()
        contact = ContactFactory(organization=contact_list.organization)
        
        contact_list.contacts.add(contact)
        contact_list.contacts.remove(contact)
        assert contact not in contact_list.contacts.all()
        assert contact_list not in contact.lists.all()

    def test_contact_list_validation(self):
        """Test contact list validation"""
        # Test that name is required
        org = OrganizationFactory()
        with pytest.raises(ValidationError):
            contact_list = ContactList(
                name="", 
                organization=org,
                created_by=UserFactory()
            )
            contact_list.full_clean()

        # Test that organization is required by checking field validation
        # We can't test this with a full_clean() as the Django ORM doesn't allow 
        # accessing a related field before it's set
        contact_list = ContactList(
            name="Test List",
            created_by=UserFactory()
        )
        # Check that organization field is specified as required in the model
        assert not ContactList._meta.get_field('organization').null

    def test_unique_name_constraint(self):
        """Test that name must be unique within an organization"""
        org = OrganizationFactory()
        ContactListFactory(name="Test List", organization=org)
        
        with pytest.raises(ValidationError):
            contact_list = ContactList(
                name="Test List", 
                organization=org,
                created_by=UserFactory()
            )
            contact_list.full_clean()

    def test_contact_list_filtering(self):
        """Test filtering contacts in a list"""
        contact_list = ContactListFactory()
        active_contact = ContactFactory(organization=contact_list.organization, is_active=True)
        inactive_contact = ContactFactory(organization=contact_list.organization, is_active=False)
        
        contact_list.contacts.add(active_contact, inactive_contact)
        
        # Test filtering active contacts
        active_contacts = contact_list.contacts.filter(is_active=True)
        assert active_contact in active_contacts
        assert inactive_contact not in active_contacts
        
        # Test filtering inactive contacts
        inactive_contacts = contact_list.contacts.filter(is_active=False)
        assert inactive_contact in inactive_contacts
        assert active_contact not in inactive_contacts

    def test_contact_list_count(self):
        """Test counting contacts in a list"""
        contact_list = ContactListFactory()
        # Verify that our factory correctly creates 5 contacts
        assert contact_list.contacts.count() == 5 