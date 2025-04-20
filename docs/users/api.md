# Users API Documentation

## Base URL
```
/api/users/
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. User Registration
Register a new user account.

**Endpoint:** `POST /register/`

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword",
    "password2": "securepassword",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "date_joined": "2024-04-19T12:00:00Z",
    "last_login": null,
    "two_factor_enabled": false,
    "backup_codes": []
}
```

### 2. User Login
Authenticate user and receive JWT tokens.

**Endpoint:** `POST /login/`

**Request Body:**
```json
{
    "username": "username",  // or "email": "user@example.com"
    "password": "securepassword"
}
```

**Response:** `200 OK`
```json
{
    "refresh": "refresh_token",
    "access": "access_token",
    "user": {
        // User object as shown in registration response
    }
}
```

If 2FA is enabled:
```json
{
    "requires_2fa": true,
    "user_id": 1,
    "message": "2FA verification required"
}
```

### 3. Two-Factor Authentication (2FA)

#### Enable 2FA
**Endpoint:** `POST /enable-2fa/`

**Response:** `200 OK`
```json
{
    "secret": "base32_secret_key",
    "qr_code": "data:image/png;base64,..."
}
```

#### Confirm 2FA Setup
**Endpoint:** `POST /confirm-2fa/`

**Request Body:**
```json
{
    "code": "123456"
}
```

#### Verify 2FA Code
**Endpoint:** `POST /verify-2fa/`

**Request Body:**
```json
{
    "user_id": 1,
    "code": "123456"
}
```

#### Disable 2FA
**Endpoint:** `POST /disable-2fa/`

**Request Body:**
```json
{
    "code": "123456"
}
```

#### Generate Backup Codes
**Endpoint:** `POST /generate-backup-codes/`

**Response:** `200 OK`
```json
{
    "backup_codes": ["code1", "code2", "code3", ...]
}
```

#### Verify Backup Code
**Endpoint:** `POST /verify-backup-code/`

**Request Body:**
```json
{
    "code": "backup_code"
}
```

### 4. Password Management

#### Change Password
**Endpoint:** `POST /change-password/`

**Authentication Required:** Yes

**Request Body:**
```json
{
    "current_password": "currentpassword",
    "new_password": "newpassword",
    "confirm_password": "newpassword"
}
```

**Response:** `200 OK`
```json
{
    "success": "Password changed successfully"
}
```

**Error Responses:**
```json
{
    "current_password": ["Current password is incorrect."]
}
```
```json
{
    "confirm_password": ["New password fields didn't match."]
}
```

#### Password Reset Request
**Endpoint:** `POST /password-reset/`

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

#### Password Reset Confirmation
**Endpoint:** `POST /password-reset-confirm/`

**Request Body:**
```json
{
    "uid": "encoded_user_id",
    "token": "reset_token",
    "new_password": "newpassword",
    "new_password2": "newpassword"
}
```

### 5. User Management

#### List Users
**Endpoint:** `GET /`

**Query Parameters:**
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        // User objects as shown in registration response
    }
]
```

#### Get User Details
**Endpoint:** `GET /<user_id>/`

**Response:** `200 OK`
```json
{
    // User object as shown in registration response
}
```

#### Update User
**Endpoint:** `PUT/PATCH /<user_id>/`

**Request Body:**
```json
{
    "first_name": "Updated",
    "last_name": "Name",
    "email": "updated@example.com"
}
```

#### Delete User (Soft Delete)
**Endpoint:** `DELETE /<user_id>/`

### 6. Filtering and Aggregation

#### Get Available Filters
**Endpoint:** `GET /available-filters/`

**Response:** `200 OK`
```json
{
    "filters": [
        // List of available filter fields and operators
    ]
}
```

#### Get Available Aggregations
**Endpoint:** `GET /available-aggregations/`

**Response:** `200 OK`
```json
{
    "aggregations": [
        // List of available aggregation functions
    ]
}
```

### 7. Token Management

#### Refresh Token
**Endpoint:** `POST /refresh-token/`

**Request Body:**
```json
{
    "refresh": "refresh_token"
}
```

**Response:** `200 OK`
```json
{
    "access": "new_access_token"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Error message describing what went wrong"
}
```

### 401 Unauthorized
```json
{
    "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
    "error": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
    "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
    "error": "An unexpected error occurred"
}
```

## Notes

1. All timestamps are in ISO 8601 format
2. Passwords must meet Django's password validation requirements
3. Email addresses must be unique
4. Usernames must be unique
5. Soft deletion is used for user deletion (sets is_active to False)
6. JWT tokens expire after a configurable time period
7. Rate limiting may be applied to certain endpoints 