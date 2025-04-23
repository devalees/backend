# Implementing User Tracking Fields in API Responses

This guide explains how to properly implement and expose `created_by` and `updated_by` user tracking fields in API responses across all Django apps in the system.

## Overview

The system uses a `UserTrackedModel` mixin from `Apps.core.models` to provide consistent user tracking functionality. This ensures that all models inheriting from this mixin automatically track which user created and updated each record.

## Implementation Steps

### 1. Ensure Models Inherit from UserTrackedModel

Make sure your model classes inherit from `UserTrackedModel`:

```python
from Apps.core.models import TimeStampedModel, UserTrackedModel

class YourModel(UserTrackedModel, TimeStampedModel):
    # Your model fields
    name = models.CharField(max_length=255)
    # ...
    
    class Meta:
        # ...
```

The `UserTrackedModel` already provides:
- `created_by` - ForeignKey to User model
- `updated_by` - ForeignKey to User model
- Automatic setting of these fields during save operations

### 2. Include Fields in Serializers

Expose these fields in your serializer to make them available in API responses:

```python
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    # Add readable user information fields
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = YourModel
        fields = (
            'id', 'name', ..., 
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
```

### 3. Set Values in ViewSet Create/Update Methods

Ensure your ViewSet properly sets the user tracking fields:

```python
from rest_framework import viewsets
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )
```

### 4. Apply Base ViewSet (Optional)

For consistency across multiple ViewSets, consider creating a base ViewSet:

```python
# In Apps.core.views
class UserTrackedViewSet(viewsets.ModelViewSet):
    """Base ViewSet that automatically sets created_by and updated_by fields"""
    
    def perform_create(self, serializer):
        user = self.request.user
        kwargs = {}
        
        # Check if model has created_by field
        if hasattr(serializer.Meta.model, 'created_by'):
            kwargs['created_by'] = user
        
        # Check if model has updated_by field
        if hasattr(serializer.Meta.model, 'updated_by'):
            kwargs['updated_by'] = user
            
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        user = self.request.user
        kwargs = {}
        
        # Check if model has updated_by field
        if hasattr(serializer.Meta.model, 'updated_by'):
            kwargs['updated_by'] = user
            
        serializer.save(**kwargs)

# Then in your app's views.py:
from Apps.core.views import UserTrackedViewSet

class YourModelViewSet(UserTrackedViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    # No need to implement perform_create/perform_update
```

### 5. Filtering and Ordering Support

Add support for filtering and ordering by user fields:

```python
class YourModelViewSet(UserTrackedViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    filterset_fields = ['name', ..., 'created_by', 'updated_by']
    ordering_fields = ['name', ..., 'created_by', 'updated_by', 'created_at', 'updated_at']
```

## Example Implementation

Here's a complete example from the Contacts app:

### Model Definition

```python
# Apps/contacts/models/contact_list.py
from django.db import models
from Apps.core.models import TimeStampedModel, UserTrackedModel
from Apps.entity.models import Organization

class ContactList(UserTrackedModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    # ... other fields
```

### Serializer Definition

```python
# Apps/contacts/serializers.py
from rest_framework import serializers
from .models import ContactList

class ContactListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ContactList
        fields = (
            'id', 'name', 'description', 'organization', 'organization_name',
            'is_active', 'created_at', 'updated_at', 
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
```

### ViewSet Definition

```python
# Apps/contacts/views.py
from rest_framework import viewsets
from .models import ContactList
from .serializers import ContactListSerializer

class ContactListViewSet(viewsets.ModelViewSet):
    queryset = ContactList.objects.all()
    serializer_class = ContactListSerializer
    
    def perform_create(self, serializer):
        """Set created_by and updated_by on create"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(
            updated_by=self.request.user
        )
```

## Best Practices

1. **Consistency**: Use the same pattern across all models/apps
2. **Read-only**: Always mark tracking fields as read-only in serializers
3. **User Names**: Include both ID and display names for better usability
4. **Default Values**: Handle null values gracefully for backward compatibility
5. **Permissions**: Consider adding permission checks for viewing sensitive user data
6. **Testing**: Ensure test coverage for user tracking functionality

## Troubleshooting

- **Missing Fields**: Ensure your model inherits from `UserTrackedModel`
- **Fields Not Updated**: Check if `perform_create` and `perform_update` are correctly implemented
- **Null Values**: Handle cases where users might be deleted after creating/updating records
- **Serialization Errors**: Ensure proper handling of null values in serializer fields

By following these guidelines, you'll ensure consistent tracking of users who created and modified records across all apps in the system. 