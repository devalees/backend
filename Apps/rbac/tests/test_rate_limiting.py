import pytest
from django.test import RequestFactory
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from ..api.middleware.rate_limiting import RateLimitMiddleware
from ..models import Role

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def request_factory():
    return RequestFactory()

@pytest.fixture
def rate_limit_middleware():
    return RateLimitMiddleware(get_response=lambda r: r)

class TestRateLimiting:
    def test_rate_limit_settings_loaded(self):
        """Test that rate limit settings are properly loaded"""
        assert hasattr(settings, 'RATE_LIMIT_ENABLED')
        assert hasattr(settings, 'RATE_LIMIT_REQUESTS')
        assert hasattr(settings, 'RATE_LIMIT_WINDOW')
        assert settings.RATE_LIMIT_ENABLED is True
        assert isinstance(settings.RATE_LIMIT_REQUESTS, int)
        assert isinstance(settings.RATE_LIMIT_WINDOW, int)

    def test_rate_limit_middleware_initialization(self, rate_limit_middleware):
        """Test that rate limit middleware initializes correctly"""
        assert rate_limit_middleware is not None
        assert hasattr(rate_limit_middleware, 'get_response')
        assert hasattr(rate_limit_middleware, 'rate_limit_storage')

    def test_rate_limit_storage_initialization(self, rate_limit_middleware):
        """Test that rate limit storage is properly initialized"""
        assert hasattr(rate_limit_middleware, 'rate_limit_storage')
        assert hasattr(rate_limit_middleware.rate_limit_storage, 'get')
        assert hasattr(rate_limit_middleware.rate_limit_storage, 'set')
        assert hasattr(rate_limit_middleware.rate_limit_storage, 'delete')

    def test_rate_limit_headers_present(self, client, request_factory):
        """Test that rate limit headers are present in response"""
        request = request_factory.get('/api/roles/')
        middleware = RateLimitMiddleware(get_response=lambda r: r)
        response = middleware(request)
        
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers

    def test_rate_limit_exceeded(self, client, request_factory):
        """Test that rate limit is enforced when exceeded"""
        # Create a request
        request = request_factory.get('/api/roles/')
        middleware = RateLimitMiddleware(get_response=lambda r: r)
        
        # Make requests up to the limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            response = middleware(request)
            assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
        
        # Next request should be rate limited
        response = middleware(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'Retry-After' in response.headers

    def test_rate_limit_reset(self, client, request_factory):
        """Test that rate limit resets after window period"""
        request = request_factory.get('/api/roles/')
        middleware = RateLimitMiddleware(get_response=lambda r: r)
        
        # Make requests up to the limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            middleware(request)
        
        # Wait for rate limit window to expire
        import time
        time.sleep(settings.RATE_LIMIT_WINDOW)
        
        # Next request should be allowed
        response = middleware(request)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_by_ip(self, client, request_factory):
        """Test that rate limit is enforced per IP address"""
        request1 = request_factory.get('/api/roles/', REMOTE_ADDR='192.168.1.1')
        request2 = request_factory.get('/api/roles/', REMOTE_ADDR='192.168.1.2')
        middleware = RateLimitMiddleware(get_response=lambda r: r)
        
        # Make requests from first IP up to the limit
        for _ in range(settings.RATE_LIMIT_REQUESTS):
            middleware(request1)
        
        # Request from second IP should still be allowed
        response = middleware(request2)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS 