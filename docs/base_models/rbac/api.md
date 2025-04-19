# Role-Based Access Control (RBAC) API Documentation

## Base URL
`/api/rbac/`

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Rate Limiting
Some endpoints are rate-limited. When limits are exceeded, you'll receive a 429 response:
```json
{
    "detail": "Request was throttled. Expected available in [time] seconds."
}
```

## Endpoints

### User Roles

#### List User Roles
```http
GET /user-roles/
```

Query Parameters:
- `user`: Filter by user ID
- `role`: Filter by role ID
- `organization`: Filter by organization ID
- `is_active`: Filter by active status
- `is_delegated`: Filter by delegation status

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "type": "users",
                "id": "1"
            },
            "role": {
                "type": "roles",
                "id": "1"
            },
            "organization": {
                "type": "organizations",
                "id": "1"
            },
            "assigned_by": {
                "type": "users",
                "id": "2"
            },
            "delegated_by": null,
            "is_active": true,
            "is_delegated": false,
            "deactivated_at": null,
            "notes": "Primary role assignment",
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    ]
}
```

#### Create User Role
```http
POST /user-roles/
```

Request Body:
```json
{
    "data": {
        "type": "user_roles",
        "attributes": {
            "user": "1",
            "role": "1",
            "notes": "Primary role assignment"
        }
    }
}
```

#### Get User Role Details
```http
GET /user-roles/{id}/
```

#### Update User Role
```http
PUT /user-roles/{id}/
PATCH /user-roles/{id}/
```

Request Body:
```json
{
    "data": {
        "type": "user_roles",
        "id": "1",
        "attributes": {
            "is_active": true,
            "notes": "Updated role assignment"
        }
    }
}
```

#### Delete User Role
```http
DELETE /user-roles/{id}/
```

#### Activate User Role
```http
POST /user-roles/{id}/activate/
```

#### Deactivate User Role
```http
POST /user-roles/{id}/deactivate/
```

#### Delegate User Role
```http
POST /user-roles/{id}/delegate/
```

Request Body:
```json
{
    "data": {
        "type": "user_roles",
        "attributes": {
            "user": "2"
        }
    }
}
```

### Roles

#### List Roles
```http
GET /api/roles/
```

Query Parameters:
- `name`: Filter by role name
- `is_active`: Filter by active status
- `parent`: Filter by parent role ID

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "roles",
            "attributes": {
                "name": "Admin",
                "description": "Administrator role",
                "is_active": true,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "permissions": {
                    "data": [
                        {
                            "type": "permissions",
                            "id": "1"
                        }
                    ]
                },
                "parent": {
                    "data": null
                },
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                }
            }
        }
    ]
}
```

#### Create Role
```http
POST /api/roles/
```

Request Body:
```json
{
    "data": {
        "type": "roles",
        "attributes": {
            "name": "Admin",
            "description": "Administrator role",
            "is_active": true,
            "permissions": ["1", "2"],
            "parent": null
        }
    }
}
```

#### Get Role Details
```http
GET /api/roles/{id}/
```

#### Update Role
```http
PUT /api/roles/{id}/
PATCH /api/roles/{id}/
```

#### Delete Role
```http
DELETE /api/roles/{id}/
```

#### Get Role Permissions
```http
GET /api/roles/{id}/permissions/
```

### Permissions

#### List Permissions
```http
GET /api/permissions/
```

Query Parameters:
- `name`: Filter by permission name
- `code`: Filter by permission code
- `is_active`: Filter by active status

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "permissions",
            "attributes": {
                "name": "Create User",
                "description": "Permission to create users",
                "code": "user.create",
                "is_active": true,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                }
            }
        }
    ]
}
```

#### Create Permission
```http
POST /api/permissions/
```

Request Body:
```json
{
    "data": {
        "type": "permissions",
        "attributes": {
            "name": "Create User",
            "description": "Permission to create users",
            "code": "user.create",
            "is_active": true
        }
    }
}
```

#### Get Permission Details
```http
GET /api/permissions/{id}/
```

#### Update Permission
```http
PUT /api/permissions/{id}/
PATCH /api/permissions/{id}/
```

#### Delete Permission
```http
DELETE /api/permissions/{id}/
```

### Resources

#### List Resources
```http
GET /api/resources/
```

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "resources",
            "attributes": {
                "name": "User Management",
                "resource_type": "module",
                "is_active": true,
                "metadata": {
                    "description": "User management module",
                    "version": "1.0"
                },
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "owner": {
                    "data": {
                        "type": "users",
                        "id": "1"
                    }
                },
                "parent": {
                    "data": null
                },
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                }
            }
        }
    ]
}
```

#### Create Resource
```http
POST /api/resources/
```

Request Body:
```json
{
    "data": {
        "type": "resources",
        "attributes": {
            "name": "User Management",
            "resource_type": "module",
            "is_active": true,
            "metadata": {
                "description": "User management module",
                "version": "1.0"
            }
        }
    }
}
```

#### Get Resource Details
```http
GET /api/resources/{id}/
```

#### Update Resource
```http
PUT /api/resources/{id}/
PATCH /api/resources/{id}/
```

#### Delete Resource
```http
DELETE /api/resources/{id}/
```

#### Grant Resource Access
```http
POST /api/resources/{id}/grant_access/
```

Request Body:
```json
{
    "data": {
        "type": "resource_accesses",
        "attributes": {
            "user": "1",
            "access_type": "read",
            "notes": "Grant read access"
        }
    }
}
```

#### Revoke Resource Access
```http
POST /api/resources/{id}/revoke_access/
```

Request Body:
```json
{
    "data": {
        "type": "resource_accesses",
        "attributes": {
            "user": "1"
        }
    }
}
```

### Resource Access

#### List Resource Access
```http
GET /api/resource-accesses/
```

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "resource_accesses",
            "attributes": {
                "access_type": "read",
                "is_active": true,
                "deactivated_at": null,
                "notes": "Read access granted",
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "resource": {
                    "data": {
                        "type": "resources",
                        "id": "1"
                    }
                },
                "user": {
                    "data": {
                        "type": "users",
                        "id": "1"
                    }
                },
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                }
            }
        }
    ]
}
```

#### Create Resource Access
```http
POST /api/resource-accesses/
```

Request Body:
```json
{
    "data": {
        "type": "resource_accesses",
        "attributes": {
            "resource": "1",
            "user": "1",
            "access_type": "read",
            "notes": "Read access granted"
        }
    }
}
```

#### Get Resource Access Details
```http
GET /api/resource-accesses/{id}/
```

#### Update Resource Access
```http
PUT /api/resource-accesses/{id}/
PATCH /api/resource-accesses/{id}/
```

#### Delete Resource Access
```http
DELETE /api/resource-accesses/{id}/
```

#### Activate Resource Access
```http
POST /api/resource-accesses/{id}/activate/
```

#### Deactivate Resource Access
```http
POST /api/resource-accesses/{id}/deactivate/
```

### Organization Context

#### List Organization Contexts
```http
GET /api/organization-contexts/
```

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "organization_contexts",
            "attributes": {
                "name": "Development",
                "description": "Development environment",
                "is_active": true,
                "deactivated_at": null,
                "metadata": {
                    "environment": "dev",
                    "region": "us-east-1"
                },
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                },
                "parent": {
                    "data": null
                }
            }
        }
    ]
}
```

#### Create Organization Context
```http
POST /api/organization-contexts/
```

Request Body:
```json
{
    "data": {
        "type": "organization_contexts",
        "attributes": {
            "name": "Development",
            "description": "Development environment",
            "is_active": true,
            "metadata": {
                "environment": "dev",
                "region": "us-east-1"
            }
        }
    }
}
```

#### Get Organization Context Details
```http
GET /api/organization-contexts/{id}/
```

#### Update Organization Context
```http
PUT /api/organization-contexts/{id}/
PATCH /api/organization-contexts/{id}/
```

#### Delete Organization Context
```http
DELETE /api/organization-contexts/{id}/
```

#### Activate Organization Context
```http
POST /api/organization-contexts/{id}/activate/
```

#### Deactivate Organization Context
```http
POST /api/organization-contexts/{id}/deactivate/
```

#### Get Organization Context Ancestors
```http
GET /api/organization-contexts/{id}/ancestors/
```

#### Get Organization Context Descendants
```http
GET /api/organization-contexts/{id}/descendants/
```

#### Get Organization Context Children
```http
GET /api/organization-contexts/{id}/children/
```

#### Get Organization Context Parents
```http
GET /api/organization-contexts/{id}/parents/
```

### Audit

#### List Audit Logs
```http
GET /audits/
```

Query Parameters:
- `user`: Filter by user ID
- `organization`: Filter by organization ID
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `status`: Filter by status
- `start_date`: Filter by start date
- `end_date`: Filter by end date

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "1",
            "type": "audits",
            "attributes": {
                "action": "create",
                "resource_type": "user",
                "resource_id": "1",
                "details": {
                    "field": "email",
                    "old_value": null,
                    "new_value": "user@example.com"
                },
                "status": "success",
                "timestamp": "2024-03-20T10:00:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "session_id": "abc123",
                "retention_period": 90,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            },
            "relationships": {
                "user": {
                    "data": {
                        "type": "users",
                        "id": "1"
                    }
                },
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": "1"
                    }
                }
            }
        }
    ]
}
```

#### Get Audit Log Details
```http
GET /audits/{id}/
```

#### Get Compliance Report
```http
GET /audits/compliance_report/
```

Query Parameters:
- `start_date`: Start date for report
- `end_date`: End date for report
- `organization`: Filter by organization ID

#### Cleanup Expired Audit Logs
```http
POST /audits/cleanup_expired/
```

## Error Responses

### 400 Bad Request
```json
{
    "errors": [
        {
            "status": "400",
            "source": {
                "pointer": "/data/attributes/field_name"
            },
            "detail": "Error message"
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

### 429 Too Many Requests
```json
{
    "errors": [
        {
            "status": "429",
            "detail": "Request was throttled. Expected available in [time] seconds."
        }
    ]
}
```

### 500 Internal Server Error
```json
{
    "errors": [
        {
            "status": "500",
            "detail": "Internal server error"
        }
    ]
}
``` 