from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

class ContactRateThrottle(UserRateThrottle):
    """Custom rate throttle for contact endpoints"""
    rate = '100/minute'  # 100 requests per minute
    scope = 'contact'
    
    def get_cache_key(self, request, view):
        """Get a unique cache key for the request"""
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
    
    def allow_request(self, request, view):
        """Check if request should be allowed"""
        if request.user.is_staff:  # Staff users are not rate limited
            return True
            
        return super().allow_request(request, view)
    
    def wait(self):
        """Return the number of seconds to wait before the next request"""
        if self.history:
            oldest_timestamp = self.history[-1]
            return max(0, 60 - (timezone.now().timestamp() - oldest_timestamp))
        return 0

class ContactCreateRateThrottle(ContactRateThrottle):
    """Stricter rate throttle for contact creation"""
    rate = '50/minute'  # 50 requests per minute
    scope = 'contact_create'

class ContactNoteRateThrottle(ContactRateThrottle):
    """Rate throttle for contact notes"""
    rate = '200/minute'  # 200 requests per minute
    scope = 'contact_note'

def get_rate_limit_headers(request, view):
    """Get rate limit headers for response"""
    throttle = view.get_throttles()[0]
    if not throttle.allow_request(request, view):
        wait = throttle.wait()
        raise Throttled(wait=wait)
    
    # Return as a dictionary that will be set individually in the view
    return {
        'X-RateLimit-Limit': str(throttle.num_requests),
        'X-RateLimit-Remaining': str(throttle.num_requests - len(throttle.history)),
        'X-RateLimit-Reset': str(int(timezone.now().timestamp() + throttle.wait()))
    } 