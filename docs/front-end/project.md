# Project API Documentation

## Base URL
All endpoints are prefixed with `/api/projects/`

## Authentication
All endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Projects

#### List Projects
- **URL**: `/projects/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `search`: Search projects by title or description
  - `ordering`: Order projects by field (prefix with - for descending)
    - Available fields: `created_at`, `start_date`, `end_date`, `status`, `priority`
  - Default ordering: `-created_at`
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of project objects

#### Get Project
- **URL**: `/projects/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Project object

#### Create Project
- **URL**: `/projects/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "title": "string",
    "description": "string",
    "start_date": "date",
    "end_date": "date",
    "status": "string",
    "priority": "string",
    "owner_id": "integer",
    "team_member_ids": ["integer"],
    "organization_id": "integer"
}
```

#### Update Project
- **URL**: `/projects/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Project
- **URL**: `/projects/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Add Team Members
- **URL**: `/projects/{id}/add_team_members/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "user_ids": ["integer"]
}
```

#### Remove Team Members
- **URL**: `/projects/{id}/remove_team_members/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "user_ids": ["integer"]
}
```

### Tasks

#### List Tasks
- **URL**: `/tasks/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `search`: Search tasks by title or description
  - `ordering`: Order tasks by field (prefix with - for descending)
    - Available fields: `created_at`, `due_date`, `status`, `priority`
  - Default ordering: `due_date`
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of task objects

#### Get Task
- **URL**: `/tasks/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Task object

#### Create Task
- **URL**: `/tasks/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "title": "string",
    "description": "string",
    "due_date": "datetime",
    "status": "string",
    "priority": "string",
    "project": "integer",
    "assigned_to_id": "integer",
    "parent_task": "integer"
}
```

#### Update Task
- **URL**: `/tasks/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Task
- **URL**: `/tasks/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Assign Task
- **URL**: `/tasks/{id}/assign/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "user_id": "integer"
}
```

#### Change Task Status
- **URL**: `/tasks/{id}/change_status/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "status": "string"
}
```

### Project Templates

#### List Project Templates
- **URL**: `/project-templates/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `search`: Search templates by title or description
  - `ordering`: Order templates by field (prefix with - for descending)
    - Available fields: `created_at`, `estimated_duration`
  - Default ordering: `-created_at`
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of project template objects

#### Get Project Template
- **URL**: `/project-templates/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Project template object

#### Create Project Template
- **URL**: `/project-templates/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "title": "string",
    "description": "string",
    "estimated_duration": "integer",
    "default_status": "string",
    "default_priority": "string",
    "organization": "integer"
}
```

#### Update Project Template
- **URL**: `/project-templates/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Project Template
- **URL**: `/project-templates/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Create Project from Template
- **URL**: `/project-templates/{id}/create_project/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "start_date": "date",
    "end_date": "date",
    "owner_id": "integer"
}
```

### Task Templates

#### List Task Templates
- **URL**: `/task-templates/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `search`: Search templates by title or description
  - `ordering`: Order templates by field (prefix with - for descending)
    - Available fields: `order`, `created_at`, `estimated_duration`
  - Default ordering: `order`, `created_at`
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of task template objects

#### Get Task Template
- **URL**: `/task-templates/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Task template object

#### Create Task Template
- **URL**: `/task-templates/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "title": "string",
    "description": "string",
    "estimated_duration": "integer",
    "default_status": "string",
    "default_priority": "string",
    "project_template": "integer",
    "parent_task_template": "integer",
    "order": "integer"
}
```

#### Update Task Template
- **URL**: `/task-templates/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Task Template
- **URL**: `/task-templates/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

## Data Models

### Project Object
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "start_date": "date",
    "end_date": "date",
    "status": "string",
    "priority": "string",
    "owner": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "team_members": [
        {
            "id": "integer",
            "username": "string",
            "email": "string"
        }
    ],
    "organization": {
        "id": "integer",
        "name": "string"
    },
    "created_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "updated_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "created_at": "datetime",
    "updated_at": "datetime",
    "tasks": ["Task Object"],
    "task_count": "integer"
}
```

### Task Object
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "due_date": "datetime",
    "status": "string",
    "priority": "string",
    "project": "integer",
    "assigned_to": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "parent_task": "integer",
    "created_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "updated_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Project Template Object
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "estimated_duration": "integer",
    "default_status": "string",
    "default_priority": "string",
    "organization": "integer",
    "task_templates": ["Task Template Object"],
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "updated_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
}
```

### Task Template Object
```json
{
    "id": "integer",
    "title": "string",
    "description": "string",
    "estimated_duration": "integer",
    "default_status": "string",
    "default_priority": "string",
    "project_template": "integer",
    "parent_task_template": "integer",
    "order": "integer",
    "subtask_templates": ["Task Template Object"],
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    },
    "updated_by": {
        "id": "integer",
        "username": "string",
        "email": "string"
    }
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