# RBAC API Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/rbac/`

## Authentication
All endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Roles

#### List Roles
- **URL**: `/roles/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by role name
  - `is_active`: Filter by active status
  - `parent`: Filter by parent role ID
- **Response**: List of roles with pagination

#### Get Role
- **URL**: `/roles/{id}/`
- **Method**: `GET`
- **Response**: Role details

#### Create Role
- **URL**: `/roles/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "parent": "integer",
    "is_active": "boolean",
    "permissions": ["integer"]
}
```

#### Update Role
- **URL**: `/roles/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Role

#### Delete Role
- **URL**: `/roles/{id}/`
- **Method**: `DELETE`

#### Role Actions
- **Get Role Permissions**
  - **URL**: `/roles/{id}/permissions/`
  - **Method**: `GET`
  - **Response**: List of permissions assigned to the role

### Permissions

#### List Permissions
- **URL**: `/permissions/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by permission name
  - `code`: Filter by permission code
  - `is_active`: Filter by active status
- **Response**: List of permissions with pagination

#### Get Permission
- **URL**: `/permissions/{id}/`
- **Method**: `GET`
- **Response**: Permission details

#### Create Permission
- **URL**: `/permissions/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "name": "string",
    "description": "string",
    "code": "string",
    "organization": "integer",
    "is_active": "boolean"
}
```

#### Update Permission
- **URL**: `/permissions/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Permission

#### Delete Permission
- **URL**: `/permissions/{id}/`
- **Method**: `DELETE`

### User Roles

#### List User Roles
- **URL**: `/user-roles/`
- **Method**: `GET`
- **Query Parameters**:
  - `user`: Filter by user ID
  - `role`: Filter by role ID
  - `organization`: Filter by organization ID
  - `is_active`: Filter by active status
  - `is_delegated`: Filter by delegation status
- **Response**: List of user roles with pagination

#### Get User Role
- **URL**: `/user-roles/{id}/`
- **Method**: `GET`
- **Response**: User role details

#### Create User Role
- **URL**: `/user-roles/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "user": "integer",
    "role": "integer",
    "organization": "integer",
    "assigned_by": "integer",
    "delegated_by": "integer",
    "is_active": "boolean",
    "is_delegated": "boolean",
    "notes": "string"
}
```

#### Update User Role
- **URL**: `/user-roles/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**:
```json
{
    "is_active": "boolean",
    "notes": "string"
}
```

#### Delete User Role
- **URL**: `/user-roles/{id}/`
- **Method**: `DELETE`

#### User Role Actions
- **Activate User Role**
  - **URL**: `/user-roles/{id}/activate/`
  - **Method**: `POST`
  - **Response**: `{"status": "role activated"}`

- **Deactivate User Role**
  - **URL**: `/user-roles/{id}/deactivate/`
  - **Method**: `POST`
  - **Response**: `{"status": "role deactivated"}`

- **Delegate User Role**
  - **URL**: `/user-roles/{id}/delegate/`
  - **Method**: `POST`
  - **Request Body**: `{"user": "integer"}`

### Resources

#### List Resources
- **URL**: `/resources/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by resource name
  - `resource_type`: Filter by resource type
  - `owner`: Filter by owner ID
  - `parent`: Filter by parent resource ID
  - `organization`: Filter by organization ID
  - `is_active`: Filter by active status
- **Response**: List of resources with pagination

#### Get Resource
- **URL**: `/resources/{id}/`
- **Method**: `GET`
- **Response**: Resource details

#### Create Resource
- **URL**: `/resources/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "name": "string",
    "resource_type": "string",
    "owner": "integer",
    "parent": "integer",
    "organization": "integer",
    "is_active": "boolean",
    "metadata": "object"
}
```

#### Update Resource
- **URL**: `/resources/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Resource

#### Delete Resource
- **URL**: `/resources/{id}/`
- **Method**: `DELETE`

#### Resource Actions
- **Grant Access**
  - **URL**: `/resources/{id}/grant_access/`
  - **Method**: `POST`
  - **Request Body**: `{"user": "integer", "access_type": "string"}`

- **Revoke Access**
  - **URL**: `/resources/{id}/revoke_access/`
  - **Method**: `POST`
  - **Request Body**: `{"user": "integer", "access_type": "string"}`

### Resource Access

#### List Resource Access
- **URL**: `/resource-accesses/`
- **Method**: `GET`
- **Query Parameters**:
  - `resource`: Filter by resource ID
  - `user`: Filter by user ID
  - `organization`: Filter by organization ID
  - `access_type`: Filter by access type
  - `is_active`: Filter by active status
- **Response**: List of resource access entries with pagination

#### Get Resource Access
- **URL**: `/resource-accesses/{id}/`
- **Method**: `GET`
- **Response**: Resource access details

#### Create Resource Access
- **URL**: `/resource-accesses/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "resource": "integer",
    "user": "integer",
    "organization": "integer",
    "access_type": "string",
    "is_active": "boolean",
    "notes": "string"
}
```

#### Update Resource Access
- **URL**: `/resource-accesses/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**:
```json
{
    "access_type": "string",
    "notes": "string"
}
```

#### Delete Resource Access
- **URL**: `/resource-accesses/{id}/`
- **Method**: `DELETE`

#### Resource Access Actions
- **Activate Resource Access**
  - **URL**: `/resource-accesses/{id}/activate/`
  - **Method**: `POST`

- **Deactivate Resource Access**
  - **URL**: `/resource-accesses/{id}/deactivate/`
  - **Method**: `POST`

### Organization Contexts

#### List Organization Contexts
- **URL**: `/organization-contexts/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by context name
  - `organization`: Filter by organization ID
  - `parent`: Filter by parent context ID
  - `is_active`: Filter by active status
- **Response**: List of organization contexts with pagination

#### Get Organization Context
- **URL**: `/organization-contexts/{id}/`
- **Method**: `GET`
- **Response**: Organization context details

#### Create Organization Context
- **URL**: `/organization-contexts/`
- **Method**: `POST`
- **Request Body**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "parent": "integer",
    "is_active": "boolean",
    "metadata": "object"
}
```

#### Update Organization Context
- **URL**: `/organization-contexts/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Organization Context

#### Delete Organization Context
- **URL**: `/organization-contexts/{id}/`
- **Method**: `DELETE`

#### Organization Context Actions
- **Activate Organization Context**
  - **URL**: `/organization-contexts/{id}/activate/`
  - **Method**: `POST`

- **Deactivate Organization Context**
  - **URL**: `/organization-contexts/{id}/deactivate/`
  - **Method**: `POST`

- **Get Ancestors**
  - **URL**: `/organization-contexts/{id}/ancestors/`
  - **Method**: `GET`
  - **Response**: List of ancestor contexts

- **Get Descendants**
  - **URL**: `/organization-contexts/{id}/descendants/`
  - **Method**: `GET`
  - **Response**: List of descendant contexts

- **Get Children**
  - **URL**: `/organization-contexts/{id}/children/`
  - **Method**: `GET`
  - **Response**: List of child contexts

- **Get Parents**
  - **URL**: `/organization-contexts/{id}/parents/`
  - **Method**: `GET`
  - **Response**: List of parent contexts

### Audit Logs

#### List Audit Logs
- **URL**: `/audits/`
- **Method**: `GET`
- **Query Parameters**:
  - `user`: Filter by user ID
  - `organization`: Filter by organization ID
  - `action`: Filter by action type
  - `resource_type`: Filter by resource type
  - `resource_id`: Filter by resource ID
  - `status`: Filter by status
- **Response**: List of audit logs with pagination

#### Get Audit Log
- **URL**: `/audits/{id}/`
- **Method**: `GET`
- **Response**: Audit log details

#### Audit Actions
- **Compliance Report**
  - **URL**: `/audits/compliance_report/`
  - **Method**: `GET`
  - **Query Parameters**:
    - `report_type`: Type of report (comprehensive, summary, etc.)
    - `start_date`: Start date for report
    - `end_date`: End date for report
  - **Response**: Compliance report data

- **Cleanup Expired**
  - **URL**: `/audits/cleanup_expired/`
  - **Method**: `POST`
  - **Response**: Cleanup results

## Data Models

### Role Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "parent": {
        "id": "integer",
        "name": "string"
    },
    "is_active": "boolean",
    "permissions": [
        {
            "id": "integer",
            "name": "string"
        }
    ],
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Permission Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "code": "string",
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### User Role Object
```json
{
    "id": "integer",
    "user": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "role": {
        "id": "integer",
        "name": "string"
    },
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "assigned_by": {
        "id": "integer",
        "username": "string"
    },
    "delegated_by": {
        "id": "integer"
    },
    "is_active": "boolean",
    "is_delegated": "boolean",
    "deactivated_at": "datetime",
    "notes": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Resource Object
```json
{
    "id": "integer",
    "name": "string",
    "resource_type": "string",
    "owner": {
        "id": "integer",
        "username": "string"
    },
    "parent": {
        "id": "integer",
        "name": "string"
    },
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "is_active": "boolean",
    "metadata": "object",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Resource Access Object
```json
{
    "id": "integer",
    "resource": {
        "id": "integer",
        "name": "string"
    },
    "user": {
        "id": "integer",
        "username": "string"
    },
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "access_type": "string",
    "is_active": "boolean",
    "deactivated_at": "datetime",
    "notes": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Organization Context Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "parent": {
        "id": "integer",
        "name": "string"
    },
    "is_active": "boolean",
    "deactivated_at": "datetime",
    "metadata": "object",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Audit Log Object
```json
{
    "id": "integer",
    "user": {
        "id": "integer",
        "username": "string"
    },
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "action": "string",
    "resource_type": "string",
    "resource_id": "integer",
    "details": "object",
    "status": "string",
    "timestamp": "datetime",
    "ip_address": "string",
    "user_agent": "string",
    "session_id": "string",
    "retention_period": "integer",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing the issue"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided"
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting
API requests are rate-limited to prevent abuse. The current limits are:
- 100 requests per minute per user
- 1000 requests per hour per user

## Pagination
List endpoints support pagination with the following parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

Response format for paginated endpoints:
```json
{
  "count": "total number of items",
  "next": "URL for next page",
  "previous": "URL for previous page",
  "results": [
    // Array of items
  ]
}
``` 