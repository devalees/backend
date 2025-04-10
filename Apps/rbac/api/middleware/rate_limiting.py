from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
import time
from typing import Callable, Dict, Any

class RateLimitStorage:
    """Storage class for rate limiting data"""
    
    def __init__(self):
        self.cache = cache
    
    def get(self, key: str) -> Dict[str, Any]:
        """Get rate limit data for a key"""
        return self.cache.get(key) or {}
    
    def set(self, key: str, data: Dict[str, Any], timeout: int) -> None:
        """Set rate limit data for a key"""
        self.cache.set(key, data, timeout)
    
    def delete(self, key: str) -> None:
        """Delete rate limit data for a key"""
        self.cache.delete(key)

class RateLimitMiddleware:
    """Middleware for rate limiting API requests"""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.rate_limit_storage = RateLimitStorage()
        
        # Default settings
        self.enabled = getattr(settings, 'RATE_LIMIT_ENABLED', True)
        self.requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # in seconds
    
    def get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')
    
    def get_rate_limit_key(self, request) -> str:
        """Generate rate limit key for the request"""
        ip = self.get_client_ip(request)
        return f'rate_limit:{ip}'
    
    def get_rate_limit_data(self, key: str) -> Dict[str, Any]:
        """Get current rate limit data"""
        data = self.rate_limit_storage.get(key)
        if not data:
            data = {
                'count': 0,
                'reset_time': int(time.time()) + self.window
            }
            self.rate_limit_storage.set(key, data, self.window)
        return data
    
    def update_rate_limit_data(self, key: str, data: Dict[str, Any]) -> None:
        """Update rate limit data"""
        data['count'] += 1
        self.rate_limit_storage.set(key, data, self.window)
    
    def is_rate_limited(self, data: Dict[str, Any]) -> bool:
        """Check if request is rate limited"""
        return data['count'] >= self.requests
    
    def get_remaining_requests(self, data: Dict[str, Any]) -> int:
        """Get number of remaining requests"""
        return max(0, self.requests - data['count'])
    
    def get_reset_time(self, data: Dict[str, Any]) -> int:
        """Get rate limit reset time"""
        return data['reset_time']
    
    def add_rate_limit_headers(self, response, data: Dict[str, Any]) -> None:
        """Add rate limit headers to response"""
        if isinstance(response, (Response, HttpResponse)):
            response['X-RateLimit-Limit'] = str(self.requests)
            response['X-RateLimit-Remaining'] = str(self.get_remaining_requests(data))
            response['X-RateLimit-Reset'] = str(self.get_reset_time(data))
    
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)
        
        key = self.get_rate_limit_key(request)
        data = self.get_rate_limit_data(key)
        
        if self.is_rate_limited(data):
            response = HttpResponse(
                'Rate limit exceeded',
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            response['Retry-After'] = str(self.get_reset_time(data))
        else:
            self.update_rate_limit_data(key, data)
            response = self.get_response(request)
            if not isinstance(response, (Response, HttpResponse)):
                response = HttpResponse(response)
        
        self.add_rate_limit_headers(response, data)
        return response 