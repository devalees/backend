import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.contact.models import Contact, ContactCategory
from Apps.users.models import User

@pytest.mark.django_db
class TestContactCategory:
    @pytest.fixture
    def category_data(self):
        return {
            'name': 'Sales Inquiry',
            'description': 'Inquiries related to sales and products',
            'is_active': True
        }

    @pytest.fixture
    def default_category(self):
        return ContactCategory.objects.create(
            name='Default',
            description='Default category for contacts',
            is_active=True
        )

    def test_create_category(self, category_data):
        category = ContactCategory.objects.create(**category_data)
        assert category.name == 'Sales Inquiry'
        assert category.description == 'Inquiries related to sales and products'
        assert category.is_active is True

    def test_category_str_representation(self, category_data):
        category = ContactCategory.objects.create(**category_data)
        assert str(category) == 'Sales Inquiry'

    def test_category_ordering(self):
        category1 = ContactCategory.objects.create(name='A Category')
        category2 = ContactCategory.objects.create(name='B Category')
        categories = list(ContactCategory.objects.all())
        assert categories[0] == category1
        assert categories[1] == category2

    def test_default_category(self, default_category):
        # Test that default category exists
        assert default_category.name == 'Default'
        assert default_category.description == 'Default category for contacts'
        assert default_category.is_active is True

        # Test that default category is unique
        with pytest.raises(Exception):
            ContactCategory.objects.create(name='Default')

@pytest.mark.django_db
class TestContact:
    @pytest.fixture
    def category(self):
        return ContactCategory.objects.create(
            name='Sales Inquiry',
            description='Sales related inquiries'
        )

    @pytest.fixture
    def valid_contact_data(self, category):
        return {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Company',
            'message': 'Test message',
            'category': category
        }

    def test_create_contact_with_category(self, valid_contact_data):
        contact = Contact.objects.create(**valid_contact_data)
        assert contact.category.name == 'Sales Inquiry'

    def test_contact_str_representation_with_category(self, valid_contact_data):
        contact = Contact.objects.create(**valid_contact_data)
        expected_str = f"{contact.first_name} {contact.last_name} ({contact.email}) - {contact.category.name}"
        assert str(contact) == expected_str

    def test_contact_type_enum(self, category):
        # Test creating a contact with entity type
        contact_entity = Contact.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            contact_type="entity",
            category=category
        )
        assert contact_entity.contact_type == "entity"
        
        # Test creating a contact with individual type
        contact_individual = Contact.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            contact_type="individual",
            category=category
        )
        assert contact_individual.contact_type == "individual"
        
        # Test invalid contact type
        with pytest.raises(ValidationError):
            Contact.objects.create(
                first_name="Invalid",
                last_name="Type",
                email="invalid@example.com",
                contact_type="invalid_type",
                category=category
            )

    def test_create_contact_without_email(self, valid_contact_data):
        # Test creating a contact without email
        contact_data = valid_contact_data.copy()
        del contact_data['email']
        contact = Contact.objects.create(**contact_data)
        assert contact.email is None
        
        # Test string representation without email
        expected_str = f"{contact.first_name} {contact.last_name} - {contact.category.name}"
        assert str(contact) == expected_str 