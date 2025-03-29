# RBAC API Documentation

## Overview
The Role-Based Access Control (RBAC) API provides endpoints for managing roles, permissions, and user assignments. It supports both model-level and field-level permissions.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Permissions

#### List Permissions
```http
GET /api/permissions/
```
Returns a list of all permissions.

**Response**
```json
{
    "count": 10,
    "next": "http://api.example.org/accounts/?page=4",
    "previous": "http://api.example.org/accounts/?page=2",
    "results": [
        {
            "id": 1,
            "name": "View User",
            "codename": "view_user",
            "description": "Can view user details",
            "created_at": "2024-03-29T12:00:00Z",
            "updated_at": "2024-03-29T12:00:00Z"
        }
    ]
}
```

#### Create Permission
```http
POST /api/permissions/
```
Creates a new permission.

**Request Body**
```json
{
    "name": "Edit User",
    "codename": "edit_user",
    "description": "Can edit user details"
}
```

### Field Permissions

#### List Field Permissions
```http
GET /api/field-permissions/
```
Returns a list of all field-level permissions.

**Response**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "content_type": {
                "id": 1,
                "app_label": "users",
                "model": "user"
            },
            "field_name": "email",
            "permission_type": "read",
            "created_at": "2024-03-29T12:00:00Z"
        }
    ]
}
```

#### Create Field Permission
```http
POST /api/field-permissions/
```
Creates a new field-level permission.

**Request Body**
```json
{
    "content_type_id": 1,
    "field_name": "email",
    "permission_type": "read"
}
```

#### Get Available Fields
```http
GET /api/field-permissions/available_fields/?content_type_id=1
```
Returns available fields for a specific model.

**Response**
```json
{
    "fields": ["id", "username", "email", "first_name", "last_name"],
    "existing_fields": ["email"]
}
```

### Roles

#### List Roles
```http
GET /api/roles/
```
Returns a list of all roles.

**Response**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Admin",
            "description": "Administrator role",
            "permissions": [...],
            "field_permissions": [...],
            "created_at": "2024-03-29T12:00:00Z",
            "updated_at": "2024-03-29T12:00:00Z"
        }
    ]
}
```

#### Create Role
```http
POST /api/roles/
```
Creates a new role.

**Request Body**
```json
{
    "name": "Editor",
    "description": "Content editor role",
    "permission_ids": [1, 2],
    "field_permission_ids": [1]
}
```

#### Assign Permissions to Role
```http
POST /api/roles/{role_id}/assign_permissions/
```
Assigns permissions to a role.

**Request Body**
```json
{
    "permission_ids": [1, 2],
    "field_permission_ids": [1]
}
```

### Role Permissions

#### List Role Permissions
```http
GET /api/role-permissions/
```
Returns a list of all role-permission relationships.

**Response**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "role": 1,
            "permission": 1,
            "field_permission": 1,
            "role_name": "Admin",
            "permission_name": "View User",
            "field_permission_details": {
                "id": 1,
                "content_type": {...},
                "field_name": "email",
                "permission_type": "read"
            },
            "created_at": "2024-03-29T12:00:00Z"
        }
    ]
}
```

### User Roles

#### List User Roles
```http
GET /api/user-roles/
```
Returns a list of all user-role assignments.

**Response**
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "role": 1,
            "role_name": "Admin",
            "username": "admin",
            "created_at": "2024-03-29T12:00:00Z"
        }
    ]
}
```

#### Create User Role
```http
POST /api/user-roles/
```
Assigns a role to a user.

**Request Body**
```json
{
    "user": 1,
    "role": 1
}
```

#### Get Current User's Roles
```http
GET /api/user-roles/my_roles/
```
Returns the current user's roles.

**Response**
```json
[
    {
        "id": 1,
        "user": 1,
        "role": 1,
        "role_name": "Admin",
        "username": "admin",
        "created_at": "2024-03-29T12:00:00Z"
    }
]
```

#### Get Current User's Field Permissions
```http
GET /api/user-roles/my_field_permissions/
```
Returns the current user's field-level permissions.

**Response**
```json
[
    {
        "id": 1,
        "content_type": {
            "id": 1,
            "app_label": "users",
            "model": "user"
        },
        "field_name": "email",
        "permission_type": "read",
        "created_at": "2024-03-29T12:00:00Z"
    }
]
```

## Error Responses
All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

## Filtering
All list endpoints support filtering using query parameters:

- `search`: Search across specified fields
- `ordering`: Order results by specified fields
- Model-specific filters as documented in each endpoint

## Pagination
All list endpoints support pagination with the following parameters:
- `page`: Page number
- `page_size`: Number of items per page

## Rate Limiting
API requests are limited to 100 requests per minute per user. 