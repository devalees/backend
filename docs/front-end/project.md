# Project API Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/project/`

## Authentication
All endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Projects

#### List Projects
- **URL**: `/projects/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in title and description
  - `ordering`: Order by created_at, start_date, end_date, status, priority
  - `status`: Filter by status (new, in_progress, on_hold, completed)
  - `priority`: Filter by priority (low, medium, high)
- **Response**: List of projects with pagination

#### Create Project
- **URL**: `/projects/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "start_date": "datetime",
    "end_date": "datetime",
    "status": "string",
    "priority": "string",
    "organization": "integer",
    "estimated_hours": "decimal"
  }
  ```

#### Get Project
- **URL**: `/projects/{id}/`
- **Method**: `GET`
- **Response**: Project details

#### Update Project
- **URL**: `/projects/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Project

#### Delete Project
- **URL**: `/projects/{id}/`
- **Method**: `DELETE`

#### Project Actions
- **Add Team Members**
  - **URL**: `/projects/{id}/add_team_members/`
  - **Method**: `POST`
  - **Request Body**: `{"user_ids": [1, 2, 3]}`

- **Remove Team Members**
  - **URL**: `/projects/{id}/remove_team_members/`
  - **Method**: `POST`
  - **Request Body**: `{"user_ids": [1, 2, 3]}`

- **Time Entries**
  - **URL**: `/projects/{id}/time_entries/`
  - **Method**: `GET`

- **Time Report**
  - **URL**: `/projects/{id}/time_report/`
  - **Method**: `GET`

- **Burndown Chart**
  - **URL**: `/projects/{id}/burndown/`
  - **Method**: `GET`

- **Time Dashboard**
  - **URL**: `/projects/{id}/time_dashboard/`
  - **Method**: `GET`

### Tasks

#### List Tasks
- **URL**: `/tasks/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in title and description
  - `ordering`: Order by created_at, due_date, status, priority
  - `status`: Filter by status (todo, in_progress, done)
  - `priority`: Filter by priority (low, medium, high)
  - `project`: Filter by project ID
  - `assigned_to`: Filter by assigned user ID

#### Create Task
- **URL**: `/tasks/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "due_date": "datetime",
    "status": "string",
    "priority": "string",
    "project": "integer",
    "assigned_to": "integer",
    "parent_task": "integer",
    "estimated_hours": "decimal"
  }
  ```

#### Get Task
- **URL**: `/tasks/{id}/`
- **Method**: `GET`

#### Update Task
- **URL**: `/tasks/{id}/`
- **Method**: `PUT/PATCH`

#### Delete Task
- **URL**: `/tasks/{id}/`
- **Method**: `DELETE`

#### Task Actions
- **Assign Task**
  - **URL**: `/tasks/{id}/assign/`
  - **Method**: `POST`
  - **Request Body**: `{"user_id": 1}`

- **Change Status**
  - **URL**: `/tasks/{id}/change_status/`
  - **Method**: `POST`
  - **Request Body**: `{"status": "string"}`

- **Time Entries**
  - **URL**: `/tasks/{id}/time_entries/`
  - **Method**: `GET`

### Project Templates

#### List Templates
- **URL**: `/project-templates/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in title and description
  - `ordering`: Order by created_at, estimated_duration

#### Create Template
- **URL**: `/project-templates/`
- **Method**: `POST`
- **Request Body**:
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

#### Template Actions
- **Create Project from Template**
  - **URL**: `/project-templates/{id}/create_project/`
  - **Method**: `POST`
  - **Request Body**: Project creation parameters

### Task Templates

#### List Templates
- **URL**: `/task-templates/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in title and description
  - `ordering`: Order by order, created_at, estimated_duration
  - `project_template`: Filter by project template ID

#### Create Template
- **URL**: `/task-templates/`
- **Method**: `POST`
- **Request Body**:
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

### Project Schedules

#### List Schedules
- **URL**: `/schedules/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in description and project title
  - `ordering`: Order by created_at, estimated_start_date, estimated_end_date, progress

#### Create Schedule
- **URL**: `/schedules/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "project": "integer",
    "estimated_start_date": "datetime",
    "estimated_end_date": "datetime",
    "description": "string",
    "is_baseline": "boolean",
    "progress": "integer",
    "estimated_hours": "decimal"
  }
  ```

#### Schedule Actions
- **Set Baseline**
  - **URL**: `/schedules/{id}/set_baseline/`
  - **Method**: `POST`

- **Get Progress**
  - **URL**: `/schedules/{id}/progress/`
  - **Method**: `GET`

### Project Phases

#### List Phases
- **URL**: `/phases/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in name and description
  - `ordering`: Order by order, start_date, end_date, progress
  - `schedule`: Filter by schedule ID

#### Create Phase
- **URL**: `/phases/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "schedule": "integer",
    "start_date": "datetime",
    "end_date": "datetime",
    "order": "integer",
    "is_active": "boolean",
    "progress": "integer",
    "estimated_hours": "decimal"
  }
  ```

#### Phase Actions
- **Reorder**
  - **URL**: `/phases/{id}/reorder/`
  - **Method**: `POST`
  - **Request Body**: `{"new_order": 1}`

- **Time Entries**
  - **URL**: `/phases/{id}/time_entries/`
  - **Method**: `GET`

### Milestones

#### List Milestones
- **URL**: `/milestones/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in name and description
  - `ordering`: Order by due_date, status
  - `schedule`: Filter by schedule ID
  - `phase`: Filter by phase ID

#### Create Milestone
- **URL**: `/milestones/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "schedule": "integer",
    "phase": "integer",
    "due_date": "datetime",
    "status": "string",
    "completion_percentage": "integer",
    "estimated_hours": "decimal"
  }
  ```

#### Milestone Actions
- **Complete**
  - **URL**: `/milestones/{id}/complete/`
  - **Method**: `POST`

- **Change Status**
  - **URL**: `/milestones/{id}/change_status/`
  - **Method**: `POST`
  - **Request Body**: `{"status": "string"}`

- **Time Entries**
  - **URL**: `/milestones/{id}/time_entries/`
  - **Method**: `GET`

### Project Discussions

#### List Discussions
- **URL**: `/projects/{project_id}/discussions/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in title and content
  - `ordering`: Order by created_at
  - `is_active`: Filter by active status

#### Create Discussion
- **URL**: `/projects/{project_id}/discussions/`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string",
    "is_active": "boolean"
  }
  ```

### Discussion Attachments

#### List Attachments
- **URL**: `/projects/{project_id}/discussions/{discussion_id}/attachments/`
- **Method**: `GET`

#### Upload Attachment
- **URL**: `/projects/{project_id}/discussions/{discussion_id}/attachments/`
- **Method**: `POST`
- **Request Body**: Multipart form data with file

### Discussion Notifications

#### List Notifications
- **URL**: `/user-notifications/`
- **Method**: `GET`
- **Query Parameters**:
  - `is_read`: Filter by read status

#### Mark Notification as Read
- **URL**: `/user-notifications/{id}/mark_read/`
- **Method**: `POST`

#### Mark All Notifications as Read
- **URL**: `/user-notifications/mark_all_read/`
- **Method**: `POST`

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