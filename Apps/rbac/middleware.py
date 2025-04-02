from django.contrib.auth import get_user_model
from django.db import transaction
from threading import local

User = get_user_model()
_thread_locals = local()

class RBACMiddleware:
    """
    Middleware that sets the current user for RBAC checks.
    This middleware should be added to MIDDLEWARE in settings.py.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set the current user in thread locals
        _thread_locals.current_user = request.user if hasattr(request, 'user') else None
        
        try:
            response = self.get_response(request)
            return response
        finally:
            # Clean up thread locals
            if hasattr(_thread_locals, 'current_user'):
                del _thread_locals.current_user

def get_current_user():
    """
    Get the current user from thread locals.
    This function should be used in model methods to get the current user.
    """
    return getattr(_thread_locals, 'current_user', None)

def set_current_user(user):
    """
    Set the current user in thread locals.
    This function should be used in background tasks or other contexts where the user is not available from the request.
    """
    _thread_locals.current_user = user

def clear_current_user():
    """
    Clear the current user from thread locals.
    This function should be used to clean up after operations that set the current user.
    """
    if hasattr(_thread_locals, 'current_user'):
        del _thread_locals.current_user 