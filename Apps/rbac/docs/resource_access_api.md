# Resource Access API Documentation

## Overview

The Resource Access API provides endpoints for managing user access to resources in the RBAC system. It allows you to create, read, update, and delete resource access entries, as well as activate and deactivate access.

## Base URL

```
/api/rbac/resource-accesses/
```

## Authentication

All endpoints require authentication. Use a valid JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### List Resource Access Entries

Retrieves a list of resource access entries.

```
GET /api/rbac/resource-accesses/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number for pagination. |
| `page_size` | integer | Number of items per page. |
| `resource_id` | integer | Filter by resource ID. |
| `user_id` | integer | Filter by user ID. |
| `access_type` | string | Filter by access type. |
| `is_active` | boolean | Filter by active status. |

#### Response

```json
{
  "data": [
    {
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

### Retrieve Resource Access Entry

Retrieves a specific resource access entry.

```
GET /api/rbac/resource-accesses/{id}/
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

### Create Resource Access Entry

Creates a new resource access entry.

```
POST /api/rbac/resource-accesses/
```

#### Request Body

```json
{
  "data": {
    "type": "resource_accesses",
    "attributes": {
      "access_type": "read",
      "is_active": true,
      "notes": ""
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

### Update Resource Access Entry

Updates a specific resource access entry.

```
PATCH /api/rbac/resource-accesses/{id}/
```

#### Request Body

```json
{
  "data": {
    "id": "1",
    "type": "resource_accesses",
    "attributes": {
      "access_type": "write",
      "notes": "Updated access level"
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
      "access_type": "write",
      "is_active": true,
      "notes": "Updated access level",
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

### Delete Resource Access Entry

Deletes a specific resource access entry.

```
DELETE /api/rbac/resource-accesses/{id}/
```

#### Response

```
204 No Content
```

### Activate Access

Activates a deactivated resource access entry.

```
POST /api/rbac/resource-accesses/{id}/activate/
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

### Deactivate Access

Deactivates an active resource access entry.

```
POST /api/rbac/resource-accesses/{id}/deactivate/
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
        "pointer": "/data/attributes/access_type"
      },
      "detail": "Invalid access type"
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
4. Use pagination for large lists of resource access entries.
5. Check permissions before performing operations on resource access entries.
6. Use the activate/deactivate endpoints instead of deleting access entries to maintain an audit trail.
7. Consider using the resource-specific grant/revoke access endpoints for simpler access management. 