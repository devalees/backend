# RBAC API Documentation

## Base URL
All endpoints are prefixed with `/api/rbac/`

## Authentication
All endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Roles

#### List Roles
- **URL**: `/roles/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `name`: Filter by role name
  - `is_active`: Filter by active status
  - `parent`: Filter by parent role ID
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of role objects

#### Get Role
- **URL**: `/roles/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Role object

#### Create Role
- **URL**: `/roles/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Role
- **URL**: `/roles/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Permissions

#### List Permissions
- **URL**: `/permissions/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `name`: Filter by permission name
  - `code`: Filter by permission code
  - `is_active`: Filter by active status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of permission objects

#### Get Permission
- **URL**: `/permissions/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Permission object

#### Create Permission
- **URL**: `/permissions/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Permission
- **URL**: `/permissions/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### User Roles

#### List User Roles
- **URL**: `/user-roles/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `user`: Filter by user ID
  - `role`: Filter by role ID
  - `organization`: Filter by organization ID
  - `is_active`: Filter by active status
  - `is_delegated`: Filter by delegation status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of user role objects

#### Get User Role
- **URL**: `/user-roles/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: User role object

#### Create User Role
- **URL**: `/user-roles/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "is_active": "boolean",
    "notes": "string"
}
```

#### Delete User Role
- **URL**: `/user-roles/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Activate User Role
- **URL**: `/user-roles/{id}/activate/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"status": "role activated"}`

#### Deactivate User Role
- **URL**: `/user-roles/{id}/deactivate/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"status": "role deactivated"}`

#### Delegate User Role
- **URL**: `/user-roles/{id}/delegate/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "user": "integer"
}
```

### Resources

#### List Resources
- **URL**: `/resources/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `name`: Filter by resource name
  - `resource_type`: Filter by resource type
  - `owner`: Filter by owner ID
  - `parent`: Filter by parent resource ID
  - `organization`: Filter by organization ID
  - `is_active`: Filter by active status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of resource objects

#### Get Resource
- **URL**: `/resources/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Resource object

#### Create Resource
- **URL**: `/resources/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Resource
- **URL**: `/resources/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Resource Access

#### List Resource Access
- **URL**: `/resource-accesses/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `resource`: Filter by resource ID
  - `user`: Filter by user ID
  - `organization`: Filter by organization ID
  - `access_type`: Filter by access type
  - `is_active`: Filter by active status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of resource access objects

#### Get Resource Access
- **URL**: `/resource-accesses/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Resource access object

#### Create Resource Access
- **URL**: `/resource-accesses/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "access_type": "string",
    "notes": "string"
}
```

#### Delete Resource Access
- **URL**: `/resource-accesses/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Organization Contexts

#### List Organization Contexts
- **URL**: `/organization-contexts/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `name`: Filter by context name
  - `organization`: Filter by organization ID
  - `parent`: Filter by parent context ID
  - `is_active`: Filter by active status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of organization context objects

#### Get Organization Context
- **URL**: `/organization-contexts/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Organization context object

#### Create Organization Context
- **URL**: `/organization-contexts/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
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
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Organization Context
- **URL**: `/organization-contexts/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Audit Logs

#### List Audit Logs
- **URL**: `/audits/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `user`: Filter by user ID
  - `organization`: Filter by organization ID
  - `action`: Filter by action type
  - `resource_type`: Filter by resource type
  - `resource_id`: Filter by resource ID
  - `status`: Filter by status
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of audit log objects

#### Get Audit Log
- **URL**: `/audits/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Audit log object

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

All endpoints may return the following error responses:

- **Code**: 400 BAD REQUEST
  - **Content**: `{"detail": "Error message"}`
- **Code**: 401 UNAUTHORIZED
  - **Content**: `{"detail": "Authentication credentials were not provided"}`
- **Code**: 403 FORBIDDEN
  - **Content**: `{"detail": "You do not have permission to perform this action"}`
- **Code**: 404 NOT FOUND
  - **Content**: `{"detail": "Not found"}`
- **Code**: 500 INTERNAL SERVER ERROR
  - **Content**: `{"detail": "Internal server error"}` 