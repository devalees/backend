import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from drf_spectacular.utils import extend_schema

class TestAPIDocumentation:
    @pytest.fixture
    def client(self):
        return APIClient()

    def test_swagger_ui_endpoint(self, client):
        """Test that the Swagger UI endpoint is accessible"""
        response = client.get('/api/schema/swagger-ui/')
        assert response.status_code == 200
        assert 'swagger-ui' in response.content.decode()

    def test_schema_endpoint(self, client):
        """Test that the OpenAPI schema endpoint is accessible"""
        response = client.get('/api/schema/')
        assert response.status_code == 200
        assert 'openapi' in response.content.decode()

    def test_schema_contains_role_endpoints(self, client):
        """Test that the schema includes Role endpoints"""
        response = client.get('/api/schema/')
        schema = response.json()
        assert '/api/roles/' in schema['paths']
        assert 'get' in schema['paths']['/api/roles/']
        assert 'post' in schema['paths']['/api/roles/']

    def test_schema_contains_permission_endpoints(self, client):
        """Test that the schema includes Permission endpoints"""
        response = client.get('/api/schema/')
        schema = response.json()
        assert '/api/permissions/' in schema['paths']
        assert 'get' in schema['paths']['/api/permissions/']
        assert 'post' in schema['paths']['/api/permissions/']

    def test_schema_contains_user_role_endpoints(self, client):
        """Test that the schema includes User-Role endpoints"""
        response = client.get('/api/schema/')
        schema = response.json()
        assert '/api/user-roles/' in schema['paths']
        assert 'get' in schema['paths']['/api/user-roles/']
        assert 'post' in schema['paths']['/api/user-roles/']

    def test_schema_contains_rate_limit_info(self, client):
        """Test that the schema includes rate limit information"""
        response = client.get('/api/schema/')
        schema = response.json()
        assert 'x-rate-limit' in schema['components']['headers']
        assert 'x-rate-limit-remaining' in schema['components']['headers']
        assert 'x-rate-limit-reset' in schema['components']['headers'] 