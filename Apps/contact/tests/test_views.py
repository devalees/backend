from django.test import TestCase, Client
from django.urls import reverse

from Apps.contact.models import Contact, ContactCategory
from Apps.users.models import User

class ContactViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact_url = reverse('contact:contact_form')
        self.category = ContactCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_contact_form_view(self):
        response = self.client.get(self.contact_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'contact/contact_form.html')

    def test_contact_form_submission(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Company',
            'message': 'Test message',
            'category': self.category.id
        }
        response = self.client.post(self.contact_url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful submission
        self.assertTrue(Contact.objects.filter(email='john@example.com').exists())

    def test_contact_form_invalid_data(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'phone': 'invalid-phone',
            'company': 'Test Company',
            'message': 'Test message',
            'category': self.category.id
        }
        response = self.client.post(self.contact_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Contact.objects.filter(first_name='John').exists()) 