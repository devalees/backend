from .models import set_current_user

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set the current user in thread local storage
        if hasattr(request, 'user'):
            set_current_user(request.user)
        
        # Process the request
        response = self.get_response(request)
        
        # Clear the current user from thread local storage
        set_current_user(None)
        
        return response 