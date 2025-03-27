from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from Apps.contact.models import Contact, ContactCategory
from Apps.users.models import User

class ContactCategoryModelTest(TestCase):
    def setUp(self):
        self.category_data = {
            'name': 'Sales Inquiry',
            'description': 'Inquiries related to sales and products',
            'is_active': True
        }
        # Create default category
        self.default_category = ContactCategory.objects.create(
            name='Default',
            description='Default category for contacts',
            is_active=True
        )

    def test_create_category(self):
        category = ContactCategory.objects.create(**self.category_data)
        self.assertEqual(category.name, 'Sales Inquiry')
        self.assertEqual(category.description, 'Inquiries related to sales and products')
        self.assertTrue(category.is_active)

    def test_category_str_representation(self):
        category = ContactCategory.objects.create(**self.category_data)
        self.assertEqual(str(category), 'Sales Inquiry')

    def test_category_ordering(self):
        category1 = ContactCategory.objects.create(name='A Category')
        category2 = ContactCategory.objects.create(name='B Category')
        categories = list(ContactCategory.objects.all())
        self.assertEqual(categories[0], category1)
        self.assertEqual(categories[1], category2)

    def test_default_category(self):
        # Test that default category exists
        default_category = ContactCategory.objects.get(name='Default')
        self.assertEqual(default_category.name, 'Default')
        self.assertEqual(default_category.description, 'Default category for contacts')
        self.assertTrue(default_category.is_active)

        # Test that default category is unique
        with self.assertRaises(Exception):
            ContactCategory.objects.create(name='Default')

class ContactModelTest(TestCase):
    def setUp(self):
        self.category = ContactCategory.objects.create(
            name='Sales Inquiry',
            description='Sales related inquiries'
        )
        self.valid_contact_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Company',
            'message': 'Test message',
            'category': self.category
        }

    def test_create_contact_with_category(self):
        contact = Contact.objects.create(**self.valid_contact_data)
        self.assertEqual(contact.category, self.category)
        self.assertEqual(contact.category.name, 'Sales Inquiry')

    def test_contact_str_representation_with_category(self):
        contact = Contact.objects.create(**self.valid_contact_data)
        expected_str = f"{contact.first_name} {contact.last_name} ({contact.email}) - {contact.category.name}"
        self.assertEqual(str(contact), expected_str)

    def test_contact_type_enum(self):
        # Test creating a contact with entity type
        contact_entity = Contact.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            contact_type="entity",
            category=self.category
        )
        self.assertEqual(contact_entity.contact_type, "entity")
        
        # Test creating a contact with individual type
        contact_individual = Contact.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            contact_type="individual",
            category=self.category
        )
        self.assertEqual(contact_individual.contact_type, "individual")
        
        # Test invalid contact type
        with self.assertRaises(ValidationError):
            Contact.objects.create(
                first_name="Invalid",
                last_name="Type",
                email="invalid@example.com",
                contact_type="invalid_type",
                category=self.category
            )

    def test_create_contact_without_email(self):
        # Test creating a contact without email
        contact_data = self.valid_contact_data.copy()
        del contact_data['email']
        contact = Contact.objects.create(**contact_data)
        self.assertIsNone(contact.email)
        
        # Test string representation without email
        expected_str = f"{contact.first_name} {contact.last_name} - {contact.category.name}"
        self.assertEqual(str(contact), expected_str) 