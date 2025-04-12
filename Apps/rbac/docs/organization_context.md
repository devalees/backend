# Organization Context

## Overview

The Organization Context is a core component of the RBAC (Role-Based Access Control) system that provides a way to group and organize resources within an organization. It enables hierarchical organization of resources and supports organization-based data isolation.

The Organization Context model allows you to:
- Create hierarchical contexts within an organization
- Group related resources together
- Implement organization-based access control
- Cache organization data for improved performance
- Manage organization-specific settings and metadata

## Model Structure

The Organization Context model extends the `RBACBaseModel` and includes the following fields:

- **name**: A unique name for the context within the organization
- **description**: A text description of the context
- **parent**: An optional reference to a parent context, enabling hierarchical organization
- **is_active**: A boolean flag indicating if the context is active
- **deactivated_at**: A timestamp recording when the context was deactivated
- **metadata**: A JSON field for storing additional context-specific data
- **organization**: A foreign key to the Organization model (inherited from RBACBaseModel)
- **created_at**: A timestamp recording when the context was created (inherited from RBACBaseModel)
- **updated_at**: A timestamp recording when the context was last updated (inherited from RBACBaseModel)

## Usage Examples

### Creating an Organization Context

```python
from Apps.rbac.models import OrganizationContext
from Apps.entity.models import Organization

# Get an organization
organization = Organization.objects.get(name="My Company")

# Create a new organization context
context = OrganizationContext.objects.create(
    organization=organization,
    name="Marketing Department",
    description="Resources for the marketing team"
)
```

### Creating a Hierarchical Context

```python
# Create a parent context
parent_context = OrganizationContext.objects.create(
    organization=organization,
    name="Marketing",
    description="Marketing department resources"
)

# Create a child context
child_context = OrganizationContext.objects.create(
    organization=organization,
    name="Social Media",
    description="Social media marketing resources",
    parent=parent_context
)
```

### Deactivating a Context

```python
# Deactivate a context
context.deactivate()

# Check if it's deactivated
print(context.is_active)  # False
print(context.deactivated_at)  # Current timestamp
```

### Activating a Context

```python
# Activate a previously deactivated context
context.activate()

# Check if it's activated
print(context.is_active)  # True
print(context.deactivated_at)  # None
```

### Getting Ancestors and Descendants

```python
# Get all ancestors of a context
ancestors = context.get_ancestors()
for ancestor in ancestors:
    print(f"Ancestor: {ancestor.name}")

# Get all descendants of a context
descendants = context.get_descendants()
for descendant in descendants:
    print(f"Descendant: {descendant.name}")

# Get all immediate children of a context
children = context.get_all_children()
for child in children:
    print(f"Child: {child.name}")

# Get all parents in the hierarchy
parents = context.get_all_parents()
for parent in parents:
    print(f"Parent: {parent.name}")
```

## API Reference

### GET /api/organization-contexts/

Retrieves a list of organization contexts.

**Response**:
```json
{
  "count": 10,
  "next": "http://api.example.org/organization-contexts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Marketing",
      "description": "Marketing department resources",
      "parent": null,
      "is_active": true,
      "organization": 1,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    ...
  ]
}
```

### POST /api/organization-contexts/

Creates a new organization context.

**Request**:
```json
{
  "name": "Sales",
  "description": "Sales department resources",
  "parent": null,
  "is_active": true,
  "organization": 1
}
```

**Response**:
```json
{
  "id": 2,
  "name": "Sales",
  "description": "Sales department resources",
  "parent": null,
  "is_active": true,
  "organization": 1,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### GET /api/organization-contexts/{id}/

Retrieves a specific organization context.

**Response**:
```json
{
  "id": 1,
  "name": "Marketing",
  "description": "Marketing department resources",
  "parent": null,
  "is_active": true,
  "organization": 1,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### PUT /api/organization-contexts/{id}/

Updates a specific organization context.

**Request**:
```json
{
  "name": "Marketing Department",
  "description": "Updated description"
}
```

**Response**:
```json
{
  "id": 1,
  "name": "Marketing Department",
  "description": "Updated description",
  "parent": null,
  "is_active": true,
  "organization": 1,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### DELETE /api/organization-contexts/{id}/

Deletes a specific organization context.

**Response**:
```json
{
  "detail": "Organization context deleted successfully"
}
```

## Best Practices

1. **Use Hierarchical Organization**: Organize contexts in a logical hierarchy that reflects your organization's structure.

2. **Keep Contexts Focused**: Each context should have a clear, specific purpose. Avoid creating contexts that are too broad or too narrow.

3. **Use Descriptive Names**: Choose names that clearly indicate the purpose of the context.

4. **Leverage Metadata**: Use the metadata field to store additional information that might be useful for your application.

5. **Implement Caching**: Use the built-in caching mechanisms to improve performance when accessing organization data.

6. **Handle Deactivation Properly**: When deactivating a context, ensure that all related resources are properly handled.

7. **Validate Context Names**: Ensure that context names are unique within an organization to avoid confusion.

8. **Document Context Purpose**: Always provide a clear description for each context to help other developers understand its purpose.

9. **Use Soft Deletion**: Prefer using the `deactivate()` method over hard deletion to maintain data history.

10. **Consider Performance**: When working with large hierarchies, be mindful of the performance implications of methods like `get_ancestors()` and `get_descendants()`. 