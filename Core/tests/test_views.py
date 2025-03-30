from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class CoreViewsTest(APITestCase):
    def test_health_check(self):
        """Test the health check endpoint returns 200 OK"""
        url = reverse('health-check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_404_handler(self):
        """Test that non-existent endpoints return proper 404 response"""
        response = self.client.get('/api/nonexistent-endpoint/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

    def test_500_handler(self):
        """Test that server errors return proper 500 response"""
        # Simulate a server error by accessing a view that raises an exception
        response = self.client.get('/api/error-test/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('detail', response.data)

    def test_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = self.client.options('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Access-Control-Allow-Origin', response)
        self.assertIn('Access-Control-Allow-Methods', response)
        self.assertIn('Access-Control-Allow-Headers', response) 