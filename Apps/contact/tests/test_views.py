import pytest
from django.test import TestCase, Client
from django.urls import reverse
from Apps.contact.models import Contact, ContactCategory
from Apps.users.models import User

@pytest.mark.django_db
class TestContactViews:
    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def contact_url(self):
        return reverse('contact:contact_form')

    @pytest.fixture
    def category(self):
        return ContactCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )

    def test_contact_form_view(self, client, contact_url):
        response = client.get(contact_url)
        assert response.status_code == 200
        assert 'contact/contact_form.html' in [t.name for t in response.templates]

    def test_contact_form_submission(self, client, contact_url, category):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'company': 'Test Company',
            'message': 'Test message',
            'category': category.id
        }
        response = client.post(contact_url, data)
        assert response.status_code == 302  # Redirect after successful submission
        assert Contact.objects.filter(email='john@example.com').exists()

    def test_contact_form_invalid_data(self, client, contact_url, category):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'phone': 'invalid-phone',
            'company': 'Test Company',
            'message': 'Test message',
            'category': category.id
        }
        response = client.post(contact_url, data)
        assert response.status_code == 200
        assert not Contact.objects.filter(first_name='John').exists() 