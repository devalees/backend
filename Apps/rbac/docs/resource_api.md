# Resource API Documentation

## Overview

The Resource API provides endpoints for managing resources in the RBAC system. It allows you to create, read, update, and delete resources, as well as manage access to resources.

## Base URL

```
/api/rbac/resources/
```

## Authentication

All endpoints require authentication. Use a valid JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### List Resources

Retrieves a list of resources.

```
GET /api/rbac/resources/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number for pagination. |
| `page_size` | integer | Number of items per page. |
| `search` | string | Search term to filter resources by name. |
| `resource_type` | string | Filter resources by type. |
| `is_active` | boolean | Filter resources by active status. |

#### Response

```json
{
  "data": [
    {
      "id": "1",
      "type": "resources",
      "attributes": {
        "name": "Project Proposal",
        "resource_type": "document",
        "is_active": true,
        "metadata": {},
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      },
      "relationships": {
        "owner": {
          "data": {
            "id": "1",
            "type": "users"
          }
        },
        "parent": {
          "data": null
        },
        "organization": {
          "data": {
            "id": "1",
            "type": "organizations"
          }
        }
      }
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "pages": 1,
      "count": 1
    }
  }
}
```

### Retrieve Resource

Retrieves a specific resource.

```
GET /api/rbac/resources/{id}/
```

#### Response

```json
{
  "data": {
    "id": "1",
    "type": "resources",
    "attributes": {
      "name": "Project Proposal",
      "resource_type": "document",
      "is_active": true,
      "metadata": {},
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    "relationships": {
      "owner": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "parent": {
        "data": null
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

### Create Resource

Creates a new resource.

```
POST /api/rbac/resources/
```

#### Request Body

```json
{
  "data": {
    "type": "resources",
    "attributes": {
      "name": "Project Proposal",
      "resource_type": "document",
      "is_active": true,
      "metadata": {}
    },
    "relationships": {
      "owner": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "parent": {
        "data": null
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

#### Response

```json
{
  "data": {
    "id": "1",
    "type": "resources",
    "attributes": {
      "name": "Project Proposal",
      "resource_type": "document",
      "is_active": true,
      "metadata": {},
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    "relationships": {
      "owner": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "parent": {
        "data": null
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

### Update Resource

Updates a specific resource.

```
PATCH /api/rbac/resources/{id}/
```

#### Request Body

```json
{
  "data": {
    "id": "1",
    "type": "resources",
    "attributes": {
      "name": "Updated Project Proposal",
      "is_active": true
    }
  }
}
```

#### Response

```json
{
  "data": {
    "id": "1",
    "type": "resources",
    "attributes": {
      "name": "Updated Project Proposal",
      "resource_type": "document",
      "is_active": true,
      "metadata": {},
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    "relationships": {
      "owner": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "parent": {
        "data": null
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

### Delete Resource

Deletes a specific resource.

```
DELETE /api/rbac/resources/{id}/
```

#### Response

```
204 No Content
```

### Grant Access

Grants access to a user for a specific resource.

```
POST /api/rbac/resources/{id}/grant_access/
```

#### Request Body

```json
{
  "data": {
    "attributes": {
      "user_id": "1",
      "access_type": "read"
    }
  }
}
```

#### Response

```json
{
  "data": {
    "id": "1",
    "type": "resource_accesses",
    "attributes": {
      "access_type": "read",
      "is_active": true,
      "notes": "",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    "relationships": {
      "resource": {
        "data": {
          "id": "1",
          "type": "resources"
        }
      },
      "user": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

### Revoke Access

Revokes access from a user for a specific resource.

```
POST /api/rbac/resources/{id}/revoke_access/
```

#### Request Body

```json
{
  "data": {
    "attributes": {
      "user_id": "1",
      "access_type": "read"
    }
  }
}
```

#### Response

```json
{
  "data": {
    "id": "1",
    "type": "resource_accesses",
    "attributes": {
      "access_type": "read",
      "is_active": false,
      "notes": "",
      "deactivated_at": "2023-01-01T00:00:00Z",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    },
    "relationships": {
      "resource": {
        "data": {
          "id": "1",
          "type": "resources"
        }
      },
      "user": {
        "data": {
          "id": "1",
          "type": "users"
        }
      },
      "organization": {
        "data": {
          "id": "1",
          "type": "organizations"
        }
      }
    }
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "errors": [
    {
      "status": "400",
      "source": {
        "pointer": "/data/attributes/name"
      },
      "detail": "Resource name cannot be empty"
    }
  ]
}
```

### 401 Unauthorized

```json
{
  "errors": [
    {
      "status": "401",
      "detail": "Authentication credentials were not provided."
    }
  ]
}
```

### 403 Forbidden

```json
{
  "errors": [
    {
      "status": "403",
      "detail": "You do not have permission to perform this action."
    }
  ]
}
```

### 404 Not Found

```json
{
  "errors": [
    {
      "status": "404",
      "detail": "Not found."
    }
  ]
}
```

## Best Practices

1. Always validate input data before sending requests.
2. Use appropriate HTTP methods for different operations.
3. Handle errors gracefully in your client application.
4. Use pagination for large lists of resources.
5. Check permissions before performing operations on resources. 