# Testing Guide

## Overview
This guide outlines our testing strategy and requirements for the API project. We use pytest for testing and Factory Boy for test data generation.

## Testing Tools
- **pytest**: Main testing framework
- **Factory Boy**: Test data generation
- **pytest-django**: Django integration for pytest
- **pytest-cov**: Coverage reporting
- **faker**: Generating realistic test data

## Coverage Requirements
- Overall coverage: Minimum 85%
- Critical components: Minimum 95%
- Models: 90%+
- Views/API Endpoints: 85%+
- Serializers: 90%+
- Utils/Helpers: 85%+

## Test Structure
1. **Test File Location**
   - Place tests in `tests/` directory within each app
   - Name test files as `test_*.py`
   - Group related tests in test classes

2. **Factory Structure**
   ```python
   # factories.py
   import factory
   from django.contrib.auth import get_user_model

   class UserFactory(factory.django.DjangoModelFactory):
       class Meta:
           model = get_user_model()

       username = factory.Sequence(lambda n: f'user{n}')
       email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
       is_active = True
   ```

3. **Test Class Structure**
   ```python
   class TestModelName:
       def setup_method(self):
           # Setup code for each test
           pass

       def teardown_method(self):
           # Cleanup code for each test
           pass

       def test_specific_functionality(self):
           # Test code
           pass
   ```

4. **API Test Structure**
   ```python
   class TestEndpointName:
       def test_list_endpoint(self, api_client, user):
           # Test GET /api/endpoint/
           pass

       def test_create_endpoint(self, api_client, user):
           # Test POST /api/endpoint/
           pass

       def test_retrieve_endpoint(self, api_client, user):
           # Test GET /api/endpoint/{id}/
           pass

       def test_update_endpoint(self, api_client, user):
           # Test PUT/PATCH /api/endpoint/{id}/
           pass

       def test_delete_endpoint(self, api_client, user):
           # Test DELETE /api/endpoint/{id}/
           pass
   ```

## Testing Best Practices

1. **Test Naming**
   - Use descriptive names that explain what is being tested
   - Follow pattern: `test_<what>_<expected_behavior>`
   - Example: `test_create_user_with_valid_data`

2. **Test Isolation**
   - Each test should be independent
   - Use Factory Boy for test data generation
   - Clean up after each test
   - Use pytest fixtures for common setup

3. **Factory Usage**
   - Create factories for all models
   - Use sequences for unique fields
   - Use LazyAttribute for dependent fields
   - Use SubFactory for related objects
   - Use traits for common variations

4. **Assertions**
   - Use pytest's assert statements
   - Test one concept per test
   - Include meaningful assertion messages
   - Use pytest's built-in assertion rewriting

5. **API Testing**
   - Test all HTTP methods
   - Test authentication/authorization
   - Test validation
   - Test error cases
   - Test response formats

## Example Test Template

```python
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .factories import UserFactory

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return UserFactory()

class TestModelName:
    def test_specific_functionality(self, user):
        # Arrange
        # Act
        # Assert
        pass

class TestEndpointName:
    def test_list_endpoint(self, api_client, user):
        # Arrange
        api_client.force_authenticate(user=user)
        
        # Act
        response = api_client.get('/api/endpoint/')
        
        # Assert
        assert response.status_code == 200
        assert len(response.data) > 0
```

## Running Tests

1. **Run all tests**
   ```bash
   pytest
   ```

2. **Run with coverage**
   ```bash
   pytest --cov=.
   ```

3. **Run specific test file**
   ```bash
   pytest path/to/test_file.py
   ```

4. **Run specific test**
   ```bash
   pytest path/to/test_file.py::TestClassName::test_method_name
   ```

5. **Run with specific marker**
   ```bash
   pytest -m "not slow"
   ```

## Coverage Reports
- Coverage reports are generated in `htmlcov/` directory
- View reports by opening `htmlcov/index.html` in a browser
- Coverage reports are required for pull requests

## Continuous Integration
- Tests must pass before merging
- Coverage must meet minimum requirements
- All new code must include tests
- Factory Boy factories must be created for all models 