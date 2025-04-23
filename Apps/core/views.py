from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = None  # This will be set later
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet that automatically sets created_by and updated_by fields
    from the request user if the model has these fields.
    """
    
    def perform_create(self, serializer):
        """
        Set created_by and updated_by on create if the model has these fields
        """
        user = self.request.user
        kwargs = {}
        
        # Check if model has created_by field
        if hasattr(serializer.Meta.model, 'created_by'):
            kwargs['created_by'] = user
            
        # Check if model has updated_by field
        if hasattr(serializer.Meta.model, 'updated_by'):
            kwargs['updated_by'] = user
            
        # Only pass kwargs if we have values to set
        if kwargs:
            serializer.save(**kwargs)
        else:
            serializer.save()
            
    def perform_update(self, serializer):
        """
        Set updated_by on update if the model has this field
        """
        user = self.request.user
        kwargs = {}
        
        # Check if model has updated_by field
        if hasattr(serializer.Meta.model, 'updated_by'):
            kwargs['updated_by'] = user
            
        # Only pass kwargs if we have values to set
        if kwargs:
            serializer.save(**kwargs)
        else:
            serializer.save() 