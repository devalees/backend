# Resource Model Documentation

## Overview

The `Resource` model is a core component of the RBAC (Role-Based Access Control) system. It represents objects that can be accessed by users with appropriate permissions. Resources can be of various types such as documents, folders, projects, tasks, users, roles, and permissions.

## Model Definition

```python
class Resource(RBACBaseModel):
    """
    Model representing a resource in the RBAC system.
    Resources are objects that can be accessed by users with appropriate permissions.
    """
    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=50)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_resources'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | The name of the resource. |
| `resource_type` | CharField | The type of the resource (e.g., 'document', 'folder', 'project', 'task', 'user', 'role', 'permission'). |
| `owner` | ForeignKey | The user who owns the resource. Can be null. |
| `parent` | ForeignKey | The parent resource. Used for hierarchical organization. Can be null. |
| `is_active` | BooleanField | Whether the resource is active. |
| `metadata` | JSONField | Additional metadata for the resource. |
| `organization` | ForeignKey | The organization the resource belongs to. Inherited from RBACBaseModel. |
| `created_at` | DateTimeField | When the resource was created. Inherited from RBACBaseModel. |
| `updated_at` | DateTimeField | When the resource was last updated. Inherited from RBACBaseModel. |

## Methods

### `__str__`

Returns a string representation of the resource.

```python
def __str__(self):
    return f"{self.name} ({self.resource_type})"
```

### `clean`

Validates resource data.

```python
def clean(self):
    """Validate resource data"""
    super().clean()
    
    # Validate resource type
    valid_resource_types = ['document', 'folder', 'project', 'task', 'user', 'role', 'permission']
    if self.resource_type not in valid_resource_types:
        raise ValidationError({
            'resource_type': _('Invalid resource type. Must be one of: %(valid_types)s') % {
                'valid_types': ', '.join(valid_resource_types)
            }
        })
    
    # Validate parent relationship
    if self.parent and self.parent.resource_type != 'folder':
        raise ValidationError({
            'parent': _('Parent resource must be of type "folder"')
        })
    
    # Validate parent organization
    if self.parent and self.parent.organization != self.organization:
        raise ValidationError({
            'parent': _('Parent resource must belong to the same organization')
        })
```

### `get_ancestors`

Returns all ancestor resources.

```python
def get_ancestors(self):
    """Get all ancestor resources"""
    ancestors = []
    current = self.parent
    while current:
        ancestors.append(current)
        current = current.parent
    return ancestors
```

### `get_descendants`

Returns all descendant resources.

```python
def get_descendants(self):
    """Get all descendant resources"""
    descendants = []
    for child in self.children.all():
        descendants.append(child)
        descendants.extend(child.get_descendants())
    return descendants
```

### `grant_access`

Grants access to a user for this resource.

```python
def grant_access(self, user, access_type):
    """
    Grant access to a user for this resource
    """
    from .models import ResourceAccess
    return ResourceAccess.objects.create(
        resource=self,
        user=user,
        access_type=access_type,
        organization=self.organization
    )
```

### `revoke_access`

Revokes access from a user for this resource.

```python
def revoke_access(self, user, access_type=None):
    """
    Revoke access from a user for this resource
    """
    from .models import ResourceAccess
    query = ResourceAccess.objects.filter(
        resource=self,
        user=user,
        organization=self.organization,
        is_active=True
    )
    
    if access_type:
        query = query.filter(access_type=access_type)
    
    for access in query:
        access.deactivate()
```

### `has_access`

Checks if a user has access to this resource.

```python
def has_access(self, user, access_type):
    """
    Check if a user has access to this resource
    """
    from .models import ResourceAccess
    return ResourceAccess.objects.filter(
        resource=self,
        user=user,
        access_type=access_type,
        organization=self.organization,
        is_active=True
    ).exists()
```

## Usage Examples

### Creating a Resource

```python
# Create a document resource
document = Resource.objects.create(
    name="Project Proposal",
    resource_type="document",
    organization=organization
)

# Create a folder resource
folder = Resource.objects.create(
    name="Project Documents",
    resource_type="folder",
    organization=organization
)

# Create a document in a folder
document_in_folder = Resource.objects.create(
    name="Requirements Document",
    resource_type="document",
    parent=folder,
    organization=organization
)
```

### Managing Resource Access

```python
# Grant read access to a user
document.grant_access(user, "read")

# Check if a user has read access
has_read_access = document.has_access(user, "read")

# Revoke read access from a user
document.revoke_access(user, "read")

# Revoke all access from a user
document.revoke_access(user)
```

### Working with Resource Hierarchy

```python
# Get all ancestors of a resource
ancestors = document_in_folder.get_ancestors()

# Get all descendants of a resource
descendants = folder.get_descendants()
```

## Best Practices

1. Always validate resource data before saving.
2. Use appropriate resource types for different objects.
3. Maintain proper resource hierarchy for better organization.
4. Grant and revoke access carefully to ensure proper security.
5. Check access before performing operations on resources. 