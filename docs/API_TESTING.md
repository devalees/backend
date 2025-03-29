# API Testing Guide

## Overview
This guide outlines how to test all aspects of the API, including endpoints, authentication, permissions, and data validation.

## Testing Categories

### 1. Authentication Testing
- Test JWT token generation
- Test token validation
- Test token expiration
- Test refresh token
- Test invalid credentials
- Test missing credentials

### 2. Authorization Testing
- Test user permissions
- Test organization access
- Test department access
- Test team access
- Test role-based access
- Test cross-organization access

### 3. Endpoint Testing
For each endpoint, test:

#### List Endpoints (GET /api/resource/)
- Test pagination
- Test filtering
- Test ordering
- Test search
- Test empty results
- Test large result sets

#### Create Endpoints (POST /api/resource/)
- Test valid data
- Test invalid data
- Test missing required fields
- Test duplicate data
- Test related object validation
- Test file uploads (if applicable)

#### Retrieve Endpoints (GET /api/resource/{id}/)
- Test existing resource
- Test non-existent resource
- Test deleted resource
- Test resource permissions
- Test related data inclusion

#### Update Endpoints (PUT/PATCH /api/resource/{id}/)
- Test full update
- Test partial update
- Test invalid updates
- Test permission changes
- Test relationship updates
- Test validation rules

#### Delete Endpoints (DELETE /api/resource/{id}/)
- Test successful deletion
- Test non-existent resource
- Test permission denied
- Test cascade deletion
- Test soft delete

### 4. Data Validation Testing
- Test field validation
- Test relationship validation
- Test business rules
- Test edge cases
- Test data constraints
- Test custom validators

### 5. Error Handling Testing
- Test 400 Bad Request
- Test 401 Unauthorized
- Test 403 Forbidden
- Test 404 Not Found
- Test 409 Conflict
- Test 500 Internal Server Error

### 6. Performance Testing
- Test response times
- Test concurrent requests
- Test large payloads
- Test database queries
- Test caching
- Test rate limiting

## Testing Tools

### 1. pytest
```bash
# Run all API tests
pytest Apps/*/tests/test_api.py

# Run specific app API tests
pytest Apps/app_name/tests/test_api.py

# Run with coverage
pytest --cov=Apps/*/views.py
```

### 2. Factory Boy
```python
# Example factory for API testing
class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Resource
    
    name = factory.Sequence(lambda n: f'Resource {n}')
    organization = factory.SubFactory(OrganizationFactory)
```

### 3. DRF Test Client
```python
# Example API test
def test_create_resource(api_client, user):
    api_client.force_authenticate(user=user)
    data = {
        'name': 'Test Resource',
        'organization': organization.id
    }
    response = api_client.post('/api/resources/', data)
    assert response.status_code == 201
```

## Testing Examples

### 1. Authentication Test
```python
def test_jwt_authentication(api_client):
    # Test token generation
    response = api_client.post('/api/token/', {
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data

    # Test token usage
    token = response.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = api_client.get('/api/protected-endpoint/')
    assert response.status_code == 200
```

### 2. Permission Test
```python
def test_organization_access(api_client, user, organization):
    # Test user's organization
    api_client.force_authenticate(user=user)
    response = api_client.get(f'/api/organizations/{organization.id}/')
    assert response.status_code == 200

    # Test other organization
    other_org = OrganizationFactory()
    response = api_client.get(f'/api/organizations/{other_org.id}/')
    assert response.status_code == 403
```

### 3. Validation Test
```python
def test_resource_validation(api_client, user):
    api_client.force_authenticate(user=user)
    
    # Test missing required field
    response = api_client.post('/api/resources/', {})
    assert response.status_code == 400
    assert 'name' in response.data

    # Test invalid data
    response = api_client.post('/api/resources/', {
        'name': '',  # Empty name
        'organization': 'invalid-id'  # Invalid organization
    })
    assert response.status_code == 400
```

## Testing Checklist

### Before Testing
- [ ] Set up test database
- [ ] Create necessary factories
- [ ] Set up test users and permissions
- [ ] Configure test environment
- [ ] Clear test data

### During Testing
- [ ] Test all endpoints
- [ ] Test all HTTP methods
- [ ] Test authentication
- [ ] Test permissions
- [ ] Test validation
- [ ] Test error cases
- [ ] Test edge cases

### After Testing
- [ ] Check coverage report
- [ ] Review error logs
- [ ] Clean up test data
- [ ] Document findings
- [ ] Update test cases

## Common Issues and Solutions

### 1. Authentication Issues
- Check token format
- Verify token expiration
- Test refresh token flow
- Check permission headers

### 2. Data Validation Issues
- Check serializer validation
- Verify model constraints
- Test custom validators
- Check relationship validation

### 3. Performance Issues
- Monitor query count
- Check response times
- Test with large datasets
- Verify caching

## Best Practices

1. **Test Organization**
   - Group related tests
   - Use descriptive names
   - Follow AAA pattern (Arrange, Act, Assert)

2. **Test Data**
   - Use factories
   - Clean up after tests
   - Use meaningful data
   - Test edge cases

3. **Test Coverage**
   - Aim for 85%+ coverage
   - Focus on critical paths
   - Test error cases
   - Test edge cases

4. **Test Maintenance**
   - Keep tests up to date
   - Remove obsolete tests
   - Document test cases
   - Review test quality 