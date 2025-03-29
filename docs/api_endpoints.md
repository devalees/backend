# API Endpoints Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/` unless otherwise specified.

## Authentication Endpoints

### User Authentication
- `POST /users/login/`
  - Login user and get tokens
  - Required Fields:
    - email (string)
    - password (string)
  - Request Body:
    ```json
    {
        "email": "string",
        "password": "string"
    }
    ```
  - Response (without 2FA):
    ```json
    {
        "refresh": "string",
        "access": "string",
        "user": {
            "id": "integer",
            "email": "string",
            "username": "string",
            // other user fields
        }
    }
    ```
  - Response (with 2FA enabled):
    ```json
    {
        "requires_2fa": true,
        "user_id": "integer",
        "message": "2FA verification required"
    }
    ```

- `POST /users/verify-2fa/`
  - Verify 2FA code and get tokens
  - Required Fields:
    - user_id (integer)
    - code (string)
  - Request Body:
    ```json
    {
        "user_id": 1,
        "code": "123456"
    }
    ```
  - Response: Same as login response without 2FA

- `POST /users/refresh-token/`
  - Refresh access token
  - Required Fields:
    - refresh (string)
  - Request Body:
    ```json
    {
        "refresh": "your_refresh_token"
    }
    ```
  - Response: `{"access": "string"}`

- `POST /users/logout/`
  - Logout user (invalidate refresh token)
  - Required Fields:
    - refresh (string)
  - Request Body:
    ```json
    {
        "refresh": "your_refresh_token"
    }
    ```
  - Response: `{"message": "Successfully logged out"}`

### Two-Factor Authentication (2FA)
- `POST /users/enable-2fa/`
  - Enable 2FA for current user
  - No request body required
  - Requires authentication

- `POST /users/confirm-2fa/`
  - Confirm and enable 2FA after verifying code
  - Required Fields:
    - code (string)
  - Request Body:
    ```json
    {
        "code": "123456"
    }
    ```
  - Response:
    ```json
    {
        "message": "2FA has been enabled successfully",
        "backup_codes": ["string"]
    }
    ```

- `POST /users/disable-2fa/`
  - Disable 2FA for current user
  - Required Fields:
    - code (string)
  - Request Body:
    ```json
    {
        "code": "123456"
    }
    ```
  - Response: `{"message": "2FA has been disabled successfully"}`

- `POST /users/generate-backup-codes/`
  - Generate new backup codes for 2FA
  - No request body required
  - Requires authentication

### Password Reset
- `POST /users/password-reset/`
  - Request password reset
  - Required Fields:
    - email (string)
  - Request Body:
    ```json
    {
        "email": "user@example.com"
    }
    ```
  - Response: `{"message": "Password reset email sent"}`

- `POST /users/password-reset-confirm/`
  - Confirm password reset
  - Required Fields:
    - uid (string)
    - token (string)
    - new_password (string)
  - Request Body:
    ```json
    {
        "uid": "MQ",
        "token": "your_reset_token",
        "new_password": "new_secure_password"
    }
    ```
  - Response: `{"message": "Password has been reset successfully"}`

## Project Management

### Projects
- `GET /projects/`
  - List all accessible projects
  - Query Parameters:
    - `search`: Search in title and description
    - `status`: Filter by status
    - `priority`: Filter by priority
    - `organization`: Filter by organization ID

- `POST /projects/`
  - Create a new project
  - Required Fields:
    - title (string)
    - start_date (date)
    - end_date (date)
    - organization_id (integer)
    - owner_id (integer)
  - Request Body:
    ```json
    {
        "title": "Project Name",
        "start_date": "2024-03-29",
        "end_date": "2024-04-29",
        "organization_id": 1,
        "owner_id": 1,
        "description": "Optional project description"
    }
    ```

- `GET /projects/{id}/`
  - Get project details

- `PUT/PATCH /projects/{id}/`
  - Update project details

- `DELETE /projects/{id}/`
  - Delete a project

- `POST /projects/{id}/add_team_members/`
  - Add team members to project
  - Required Fields:
    - user_ids (array of integers)
  - Request Body:
    ```json
    {
        "user_ids": [1, 2, 3]
    }
    ```

- `POST /projects/{id}/remove_team_members/`
  - Remove team members from project
  - Required Fields:
    - user_ids (array of integers)
  - Request Body:
    ```json
    {
        "user_ids": [1, 2, 3]
    }
    ```

### Tasks
- `GET /tasks/`
  - List all accessible tasks
  - Query Parameters:
    - `project`: Filter by project ID
    - `status`: Filter by status
    - `priority`: Filter by priority
    - `assigned_to`: Filter by assignee ID

- `POST /tasks/`
  - Create a new task
  - Required Fields:
    - title (string)
    - due_date (date)
    - project (integer)
  - Request Body:
    ```json
    {
        "title": "Task Name",
        "due_date": "2024-04-01",
        "project": 1,
        "description": "Optional task description",
        "priority": "medium"
    }
    ```

- `GET /tasks/{id}/`
  - Get task details

- `PUT/PATCH /tasks/{id}/`
  - Update task details

- `DELETE /tasks/{id}/`
  - Delete a task

- `POST /tasks/{id}/assign/`
  - Assign task to user
  - Required Fields:
    - user_id (integer)
  - Request Body:
    ```json
    {
        "user_id": 1
    }
    ```

- `POST /tasks/{id}/change_status/`
  - Update task status
  - Required Fields:
    - status (string)
  - Request Body:
    ```json
    {
        "status": "done"
    }
    ```

### Project Templates
- `GET /project-templates/`
  - List all accessible project templates

- `POST /project-templates/`
  - Create a new project template
  - Required Fields:
    - title (string)
    - estimated_duration (integer)
    - organization (integer)
  - Request Body:
    ```json
    {
        "title": "Template Name",
        "estimated_duration": 30,
        "organization": 1,
        "description": "Optional template description"
    }
    ```

- `GET /project-templates/{id}/`
  - Get template details

- `PUT/PATCH /project-templates/{id}/`
  - Update template details

- `DELETE /project-templates/{id}/`
  - Delete a template

- `POST /project-templates/{id}/create_project/`
  - Create project from template
  - Required Fields:
    - start_date (datetime)
    - end_date (datetime)
    - owner_id (integer)
  - Request Body:
    ```json
    {
        "start_date": "2024-03-29T00:00:00Z",
        "end_date": "2024-04-29T00:00:00Z",
        "owner_id": 1
    }
    ```

### Task Templates
- `GET /task-templates/`
  - List all accessible task templates

- `POST /task-templates/`
  - Create a new task template
  - Required Fields:
    - title (string)
    - estimated_duration (integer)
    - project_template (integer)
  - Request Body:
    ```json
    {
        "title": "Task Template Name",
        "estimated_duration": 7,
        "project_template": 1,
        "description": "Optional task template description"
    }
    ```

- `GET /task-templates/{id}/`
  - Get task template details

- `PUT/PATCH /task-templates/{id}/`
  - Update task template details

- `DELETE /task-templates/{id}/`
  - Delete a task template

## User Management

### Users
- `GET /users/`
  - List all users
  - Query Parameters:
    - `search`: Search in username and email
    - `organization`: Filter by organization ID

- `POST /users/`
  - Create a new user
  - Required Fields:
    - username (string)
    - email (string)
    - password (string)
    - password2 (string) - Must match password
  - Request Body:
    ```json
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "secure_password",
        "password2": "secure_password",
        "first_name": "Optional First",
        "last_name": "Optional Last"
    }
    ```

- `GET /users/{id}/`
  - Get user details

- `PUT/PATCH /users/{id}/`
  - Update user details

- `DELETE /users/{id}/`
  - Delete a user

- `GET /users/me/`
  - Get current user details

### Organizations
- `GET /organizations/`
  - List all accessible organizations

- `POST /organizations/`
  - Create a new organization
  - Required Fields:
    - name (string)
  - Request Body:
    ```json
    {
        "name": "Organization Name",
        "description": "Optional organization description"
    }
    ```

- `GET /organizations/{id}/`
  - Get organization details

- `PUT/PATCH /organizations/{id}/`
  - Update organization details

- `DELETE /organizations/{id}/`
  - Delete an organization

### Teams
- `GET /teams/`
  - List all accessible teams

- `POST /teams/`
  - Create a new team
  - Required Fields:
    - name (string)
    - organization (integer)
  - Request Body:
    ```json
    {
        "name": "Team Name",
        "organization": 1,
        "description": "Optional team description"
    }
    ```

- `GET /teams/{id}/`
  - Get team details

- `PUT/PATCH /teams/{id}/`
  - Update team details

- `DELETE /teams/{id}/`
  - Delete a team

## Contact Management

### Contacts
- `GET /contacts/`
  - List all contacts
  - Query Parameters:
    - `search`: Search in name and email
    - `organization`: Filter by organization ID

- `POST /contacts/`
  - Create a new contact
  - Required Fields:
    - name (string)
    - email (string)
    - organization (integer)
  - Request Body:
    ```json
    {
        "name": "Contact Name",
        "email": "contact@example.com",
        "organization": 1,
        "phone": "Optional phone number"
    }
    ```

- `GET /contacts/{id}/`
  - Get contact details

- `PUT/PATCH /contacts/{id}/`
  - Update contact details

- `DELETE /contacts/{id}/`
  - Delete a contact

## Data Transfer

### Import/Export
- `POST /data-transfer/import/`
  - Import data
  - Required Fields:
    - file (multipart/form-data)
    - format (string: "csv" or "json")
  - Request Body:
    ```
    Content-Type: multipart/form-data
    
    file: <your_file>
    format: "csv"
    ```

- `GET /data-transfer/export/`
  - Export data
  - Query Parameters:
    - `format`: Export format (csv, json)
    - `model`: Model to export (projects, tasks, contacts)

## Common Features

### All List Endpoints Support:
- Pagination
  - `page`: Page number
  - `page_size`: Items per page
- Ordering
  - `ordering`: Field to order by (prefix with `-` for descending)
- Filtering
  - Model-specific filters
- Search
  - `search`: Search term for supported fields

### Authentication Required
All endpoints except authentication endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Response Formats
All endpoints return JSON responses with the following structure:
- Success Response:
  ```json
  {
    "data": {},
    "message": "string",
    "status": "success"
  }
  ```
- Error Response:
  ```json
  {
    "error": "string",
    "message": "string",
    "status": "error"
  }
  ```

### Common Status Codes
- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error 