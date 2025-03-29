# RBAC Integration Guide

## Overview
This guide explains how to integrate the Role-Based Access Control (RBAC) system into your Django application. The system supports both model-level and field-level permissions.

## Installation

1. Add the RBAC app to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'Apps.rbac',
]
```

2. Add the RBAC URLs to your main URLs configuration:
```python
urlpatterns = [
    ...
    path('api/', include('Apps.rbac.urls')),
]
```

3. Run migrations:
```bash
python manage.py makemigrations rbac
python manage.py migrate
```

## Basic Usage

### Checking Permissions

1. Using the utility functions:
```python
from Apps.rbac.utils import has_permission, has_role

# Check model-level permission
if has_permission(user, 'view_user'):
    # Allow access

# Check field-level permission
if has_permission(user, 'read', model=User, field='email'):
    # Allow access to email field

# Check role
if has_role(user, 'admin'):
    # Allow admin actions
```

2. Using the decorators:
```python
from Apps.rbac.utils import require_permission, require_role

@require_permission('edit_user')
def edit_user_view(request):
    # Only users with edit_user permission can access this

@require_permission('read', model=User, field='email')
def view_email_view(request):
    # Only users with read permission on email field can access this

@require_role('admin')
def admin_view(request):
    # Only users with admin role can access this
```

### Using in Serializers

1. Filter fields based on permissions:
```python
from rest_framework import serializers
from Apps.rbac.utils import get_field_permissions

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context['request'].user
        field_perms = get_field_permissions(user, User)
        
        # Only include fields the user has read permission for
        return {
            field: value
            for field, value in data.items()
            if field_perms.get(field) == 'read'
        }
```

2. Validate field access in create/update:
```python
class UserSerializer(serializers.ModelSerializer):
    def validate(self, data):
        user = self.context['request'].user
        field_perms = get_field_permissions(user, User)
        
        for field, value in data.items():
            if field_perms.get(field) != 'write':
                raise serializers.ValidationError(
                    f"You don't have permission to modify the {field} field"
                )
        return data
```

### Using in Views

1. Check permissions in view methods:
```python
from rest_framework import viewsets
from Apps.rbac.utils import has_permission

class UserViewSet(viewsets.ModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        if not has_permission(request.user, 'view_user'):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not has_permission(request.user, 'edit_user'):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
```

2. Using permission classes:
```python
from rest_framework import viewsets
from Apps.rbac.permissions import CanManageRoles

class RoleViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageRoles]
    # ... rest of the viewset
```

## Field-Level Permissions

### Creating Field Permissions

1. Using the admin interface:
   - Navigate to the Field Permissions section
   - Select the model (content type)
   - Enter the field name
   - Select the permission type (read, write, create, delete)

2. Using the API:
```python
from django.contrib.contenttypes.models import ContentType
from Apps.rbac.models import FieldPermission

# Create field permission
content_type = ContentType.objects.get_for_model(User)
field_permission = FieldPermission.objects.create(
    content_type=content_type,
    field_name='email',
    permission_type='read',
    created_by=admin_user
)
```

### Assigning Field Permissions to Roles

1. Using the admin interface:
   - Navigate to the Role section
   - Edit a role
   - Add field permissions in the Role Permissions inline

2. Using the API:
```python
from Apps.rbac.models import RolePermission

# Assign field permission to role
RolePermission.objects.create(
    role=role,
    permission=permission,
    field_permission=field_permission,
    created_by=admin_user
)
```

## Best Practices

1. **Permission Naming**
   - Use clear, descriptive permission names
   - Follow the pattern: `action_model` (e.g., `view_user`, `edit_post`)
   - Keep codenames lowercase with underscores

2. **Role Organization**
   - Create roles based on job functions
   - Use hierarchical roles when needed
   - Keep role names simple and clear

3. **Field Permissions**
   - Only create field permissions for sensitive fields
   - Use appropriate permission types (read, write, create, delete)
   - Consider performance impact when using field permissions

4. **Testing**
   - Test both model-level and field-level permissions
   - Test permission inheritance through roles
   - Test edge cases and error conditions

## Security Considerations

1. **Permission Caching**
   - The system caches permissions for performance
   - Clear cache when permissions change:
   ```python
   from django.core.cache import cache
   cache.delete(f'user_permissions_{user.id}')
   ```

2. **Audit Logging**
   - All permission changes are logged
   - Track who made changes and when
   - Monitor for suspicious activity

3. **Rate Limiting**
   - API endpoints are rate-limited
   - Monitor for abuse
   - Adjust limits as needed

## Troubleshooting

1. **Permission Not Working**
   - Check if user has the correct role
   - Verify role has the required permission
   - Check field permission configuration
   - Clear permission cache

2. **Performance Issues**
   - Monitor permission cache hits/misses
   - Optimize field permission queries
   - Use bulk operations when possible

3. **Common Errors**
   - Invalid permission codename
   - Missing field in model
   - Incorrect content type
   - Cache inconsistencies

## Support

For additional support:
1. Check the API documentation
2. Review the test cases
3. Contact the development team
4. Submit issues through the issue tracker 