# Users API Documentation

## Base URL
All endpoints are prefixed with `/api/users/`

## Authentication
Most endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Authentication

#### Login
- **URL**: `/login`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "username": "string", // or "email": "string"
    "password": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "refresh": "string",
    "access": "string",
    "user": {
        "id": "integer",
        "email": "string",
        "username": "string",
        "first_name": "string",
        "last_name": "string",
        "is_active": "boolean",
        "is_staff": "boolean",
        "is_superuser": "boolean",
        "date_joined": "datetime",
        "last_login": "datetime",
        "two_factor_enabled": "boolean",
        "backup_codes": ["string"]
    }
}
```
- **Error Response**:
  - **Code**: 401 UNAUTHORIZED
  - **Content**: `{"error": "Invalid credentials"}`
  - **Code**: 400 BAD REQUEST
  - **Content**: `{"error": "Please provide either username or email"}`

#### Register
- **URL**: `/register`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "email": "string",
    "username": "string",
    "password": "string",
    "password2": "string",
    "first_name": "string",
    "last_name": "string"
}
```
- **Success Response**:
  - **Code**: 201 CREATED
  - **Content**: User object
- **Error Response**:
  - **Code**: 400 BAD REQUEST
  - **Content**: `{"error": "Validation error details"}`

#### Refresh Token
- **URL**: `/refresh_token`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "refresh": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "access": "string"
}
```

#### Logout
- **URL**: `/logout`
- **Method**: `POST`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"message": "Successfully logged out"}`

### Two-Factor Authentication (2FA)

#### Enable 2FA
- **URL**: `/enable_2fa`
- **Method**: `POST`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "secret": "string",
    "qr_code": "string",
    "totp_uri": "string",
    "manual_entry_code": "string",
    "message": "string",
    "instructions": ["string"]
}
```

#### Confirm 2FA
- **URL**: `/confirm_2fa`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "code": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "message": "2FA has been enabled successfully",
    "backup_codes": ["string"]
}
```

#### Verify 2FA
- **URL**: `/verify_2fa`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "user_id": "integer",
    "code": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Same as login response

#### Disable 2FA
- **URL**: `/disable_2fa`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "code": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"message": "2FA has been disabled successfully"}`

#### Generate Backup Codes
- **URL**: `/generate_backup_codes`
- **Method**: `POST`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "backup_codes": ["string"]
}
```

#### Verify Backup Code
- **URL**: `/verify_backup_code`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "code": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Same as login response

### Password Management

#### Password Reset Request
- **URL**: `/password_reset`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "email": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"message": "Password reset email has been sent"}`

#### Password Reset Confirm
- **URL**: `/password_reset_confirm`
- **Method**: `POST`
- **Auth Required**: No
- **Data Constraints**:
```json
{
    "uid": "string",
    "token": "string",
    "password": "string",
    "password2": "string"
}
```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: `{"message": "Password has been reset successfully"}`

### User Management

#### List Users
- **URL**: `/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of user objects
- **Note**: Regular users can only see their own profile. Superusers can see all users.

#### Get User
- **URL**: `/{id}`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: User object

#### Update User
- **URL**: `/{id}`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as register
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Updated user object

#### Delete User
- **URL**: `/{id}`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 204 NO CONTENT
- **Note**: This performs a soft delete by setting is_active to false

## Error Responses

All endpoints may return the following error responses:

- **Code**: 400 BAD REQUEST
  - **Content**: `{"error": "Error message"}`
- **Code**: 401 UNAUTHORIZED
  - **Content**: `{"error": "Authentication credentials were not provided"}`
- **Code**: 403 FORBIDDEN
  - **Content**: `{"error": "You do not have permission to perform this action"}`
- **Code**: 404 NOT FOUND
  - **Content**: `{"error": "Not found"}`
- **Code**: 500 INTERNAL SERVER ERROR
  - **Content**: `{"error": "Internal server error"}`

## Data Models

### User Object
```json
{
    "id": "integer",
    "email": "string",
    "username": "string",
    "first_name": "string",
    "last_name": "string",
    "is_active": "boolean",
    "is_staff": "boolean",
    "is_superuser": "boolean",
    "date_joined": "datetime",
    "last_login": "datetime",
    "two_factor_enabled": "boolean",
    "backup_codes": ["string"],
    "created_by": "integer"
}
``` 