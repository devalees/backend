import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView
from Apps.contacts.models import Contact
from Apps.entity.models import Organization
import yaml

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user

@pytest.fixture
def test_organization():
    org = Organization.objects.create(
        name='Test Org',
        description='Test Organization'
    )
    return org

@pytest.mark.django_db
class TestAPIDocumentation:
    """Test cases for API documentation"""
    
    def test_schema_endpoint_accessible(self, api_client, test_user):
        """Test that the schema endpoint is accessible"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'application/vnd.oai.openapi' in response['Content-Type']
        
    def test_schema_contains_contact_endpoints(self, api_client, test_user):
        """Test that contact endpoints are documented in schema"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for contact endpoints
        paths = schema.get('paths', {})
        # Look for any paths that include 'contacts'
        contact_paths = [path for path in paths.keys() if 'contacts' in path.lower()]
        assert len(contact_paths) > 0, "No contact endpoints found in schema"
        
    def test_schema_contains_request_response_examples(self, api_client, test_user):
        """Test that endpoints have request/response examples"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for examples in components or paths
        schema_str = str(schema)
        assert 'example' in schema_str, "No examples found in schema"
        
    def test_schema_contains_authentication_info(self, api_client, test_user):
        """Test that authentication information is documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for security schemes
        assert 'components' in schema
        assert 'securitySchemes' in schema['components']
        
    def test_schema_contains_error_responses(self, api_client, test_user):
        """Test that error responses are documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for error responses
        schema_str = str(schema)
        assert '400' in schema_str, "No 400 error responses found in schema"
        assert '401' in schema_str, "No 401 error responses found in schema"
        
    def test_schema_contains_rate_limit_info(self, api_client, test_user):
        """Test that rate limit information is documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for rate limit information - either in a header or component
        schema_str = str(schema)
        assert 'RateLimit' in schema_str or 'rate limit' in schema_str.lower()
        
    def test_schema_contains_field_descriptions(self, api_client, test_user):
        """Test that field descriptions are documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for field descriptions in schemas
        components = schema.get('components', {})
        schemas = components.get('schemas', {})
        # Just check if any schema has description
        has_description = False
        for schema_name, schema_def in schemas.items():
            if 'properties' in schema_def:
                for prop_name, prop_def in schema_def['properties'].items():
                    if isinstance(prop_def, dict) and 'description' in prop_def:
                        has_description = True
                        break
            if has_description:
                break
                
        assert has_description, "No field descriptions found in schema"
        
    def test_schema_contains_query_parameters(self, api_client, test_user):
        """Test that query parameters are documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for parameters in any endpoint
        paths = schema.get('paths', {})
        # Check if any endpoint has parameters
        has_parameters = False
        for path_data in paths.values():
            for method_data in path_data.values():
                if 'parameters' in method_data:
                    has_parameters = True
                    break
            if has_parameters:
                break
        assert has_parameters, "No query parameters found in schema"
        
    def test_schema_contains_filter_options(self, api_client, test_user):
        """Test that filter options are documented"""
        api_client.force_authenticate(user=test_user)
        url = reverse('schema')
        response = api_client.get(url)
        schema = yaml.safe_load(response.content.decode('utf-8'))
        
        # Check for filter parameters in any endpoint
        paths = schema.get('paths', {})
        # Look for any path that has filter parameters like 'search' or parameters with 'in': 'query'
        has_filter = False
        for path_data in paths.values():
            for method_data in path_data.values():
                if 'parameters' in method_data:
                    for param in method_data['parameters']:
                        if isinstance(param, dict) and (
                            param.get('in') == 'query' or 
                            param.get('name') in ['search', 'filter', 'ordering']
                        ):
                            has_filter = True
                            break
            if has_filter:
                break
        assert has_filter, "No filter options found in schema" 