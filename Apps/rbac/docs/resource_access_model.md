# ResourceAccess Model Documentation

## Overview

The `ResourceAccess` model is a key component of the RBAC (Role-Based Access Control) system. It represents the access permissions that users have to resources. Each instance of `ResourceAccess` defines a specific type of access (read, write, delete, admin) that a user has to a particular resource.

## Model Definition

```python
class ResourceAccess(RBACBaseModel):
    """
    Model representing access to a resource by a user.
    Defines the type of access (read, write, etc.) and tracks access status.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='access_entries'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_access'
    )
    access_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `resource` | ForeignKey | The resource this access entry applies to. |
| `user` | ForeignKey | The user who has access to the resource. |
| `access_type` | CharField | The type of access (e.g., 'read', 'write', 'delete', 'admin'). |
| `is_active` | BooleanField | Whether this access entry is active. |
| `deactivated_at` | DateTimeField | When this access entry was deactivated. Null if active. |
| `notes` | TextField | Additional notes about this access entry. |
| `organization` | ForeignKey | The organization this access entry belongs to. Inherited from RBACBaseModel. |
| `created_at` | DateTimeField | When this access entry was created. Inherited from RBACBaseModel. |
| `updated_at` | DateTimeField | When this access entry was last updated. Inherited from RBACBaseModel. |

## Methods

### `__str__`

Returns a string representation of the resource access entry.

```python
def __str__(self):
    return f"{self.user.username} - {self.resource.name} ({self.access_type})"
```

### `clean`

Validates resource access data.

```python
def clean(self):
    """Validate resource access data"""
    super().clean()
    
    # Validate access type
    valid_access_types = ['read', 'write', 'delete', 'admin']
    if self.access_type not in valid_access_types:
        raise ValidationError({
            'access_type': _('Invalid access type. Must be one of: %(valid_types)s') % {
                'valid_types': ', '.join(valid_access_types)
            }
        })
    
    # Validate resource organization
    if self.resource.organization != self.organization:
        raise ValidationError({
            'resource': _('Resource must belong to the same organization')
        })
    
    # Validate user organization
    from Apps.entity.models import TeamMember
    if not TeamMember.objects.filter(user=self.user, team__department__organization=self.organization).exists():
        raise ValidationError({
            'user': _('User must belong to the organization')
        })
```

### `deactivate`

Deactivates this access entry.

```python
def deactivate(self):
    """Deactivate this access entry"""
    self.is_active = False
    self.deactivated_at = timezone.now()
    self.save()
```

### `activate`

Activates this access entry.

```python
def activate(self):
    """Activate this access entry"""
    self.is_active = True
    self.deactivated_at = None
    self.save()
```

## Usage Examples

### Creating a Resource Access Entry

```python
# Create a resource access entry
resource_access = ResourceAccess.objects.create(
    resource=document,
    user=user,
    access_type="read",
    organization=organization
)
```

### Managing Resource Access

```python
# Deactivate a resource access entry
resource_access.deactivate()

# Activate a resource access entry
resource_access.activate()

# Update notes for a resource access entry
resource_access.notes = "Access granted for project review"
resource_access.save()
```

### Querying Resource Access

```python
# Get all active read access entries for a resource
read_access = ResourceAccess.objects.filter(
    resource=document,
    access_type="read",
    is_active=True
)

# Get all access entries for a user
user_access = ResourceAccess.objects.filter(
    user=user,
    is_active=True
)

# Get all access entries for a resource
resource_access = ResourceAccess.objects.filter(
    resource=document,
    is_active=True
)
```

## Best Practices

1. Always validate resource access data before saving.
2. Use appropriate access types for different operations.
3. Deactivate access entries instead of deleting them to maintain an audit trail.
4. Check access before performing operations on resources.
5. Use the `grant_access` and `revoke_access` methods on the `Resource` model for simpler access management. 