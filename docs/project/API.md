# Project Management API Documentation

## Overview
This document provides detailed information about the Project Management API endpoints, their functionality, and usage.

## Authentication
All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
All endpoints are relative to the base URL: `/api/project/`

## Endpoints

### Projects

#### List Projects
- **URL**: `/projects/`
- **Method**: `GET`
- **Description**: Retrieve a list of projects
- **Query Parameters**:
  - `search`: Search projects by title or description
  - `ordering`: Order by field (created_at, start_date, end_date, status, priority)
- **Response**: List of projects with their details

#### Create Project
- **URL**: `/projects/`
- **Method**: `POST`
- **Description**: Create a new project
- **Request Body**:
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
- **Response**: Created project details

#### Get Project
- **URL**: `/projects/{id}/`
- **Method**: `GET`
- **Description**: Retrieve a specific project
- **Response**: Project details

#### Update Project
- **URL**: `/projects/{id}/`
- **Method**: `PUT/PATCH`
- **Description**: Update a project
- **Request Body**: Same as Create Project
- **Response**: Updated project details

#### Delete Project
- **URL**: `/projects/{id}/`
- **Method**: `DELETE`
- **Description**: Delete a project

#### Project Actions

##### Add Team Members
- **URL**: `/projects/{id}/add_team_members/`
- **Method**: `POST`
- **Description**: Add members to project team
- **Request Body**:
  ```json
  {
    "user_ids": ["integer"]
  }
  ```

##### Remove Team Members
- **URL**: `/projects/{id}/remove_team_members/`
- **Method**: `POST`
- **Description**: Remove members from project team
- **Request Body**:
  ```json
  {
    "user_ids": ["integer"]
  }
  ```

##### Time Entries
- **URL**: `/projects/{id}/time_entries/`
- **Method**: `GET`
- **Description**: Get time entries for project
- **Query Parameters**:
  - `task_id`: Filter by task
  - `phase_id`: Filter by phase
  - `milestone_id`: Filter by milestone
  - `user_id`: Filter by user
  - `is_billable`: Filter by billable status
  - `start_date`: Filter by start date
  - `end_date`: Filter by end date

##### Time Report
- **URL**: `/projects/{id}/time_report/`
- **Method**: `GET`
- **Description**: Get time report with statistics
- **Query Parameters**:
  - `start_date`: Report start date
  - `end_date`: Report end date

### Tasks

#### List Tasks
- **URL**: `/tasks/`
- **Method**: `GET`
- **Description**: Retrieve a list of tasks
- **Query Parameters**:
  - `search`: Search tasks by title or description
  - `ordering`: Order by field (created_at, due_date, status, priority)
- **Response**: List of tasks with their details

#### Create Task
- **URL**: `/tasks/`
- **Method**: `POST`
- **Description**: Create a new task
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "due_date": "date",
    "status": "string",
    "priority": "string",
    "project": "integer",
    "assigned_to_id": "integer",
    "parent_task": "integer"
  }
  ```
- **Response**: Created task details

#### Task Actions

##### Assign Task
- **URL**: `/tasks/{id}/assign/`
- **Method**: `POST`
- **Description**: Assign task to a user
- **Request Body**:
  ```json
  {
    "user_id": "integer"
  }
  ```

##### Change Task Status
- **URL**: `/tasks/{id}/change_status/`
- **Method**: `POST`
- **Description**: Change task status
- **Request Body**:
  ```json
  {
    "status": "string"
  }
  ```

### Project Templates

#### List Project Templates
- **URL**: `/project-templates/`
- **Method**: `GET`
- **Description**: Retrieve a list of project templates
- **Query Parameters**:
  - `search`: Search templates by title or description
  - `ordering`: Order by field (created_at, estimated_duration)
- **Response**: List of project templates

#### Create Project Template
- **URL**: `/project-templates/`
- **Method**: `POST`
- **Description**: Create a new project template
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
- **Response**: Created template details

#### Template Actions

##### Create Project from Template
- **URL**: `/project-templates/{id}/create_project/`
- **Method**: `POST`
- **Description**: Create a new project from template
- **Request Body**:
  ```json
  {
    "start_date": "date",
    "end_date": "date"
  }
  ```

### Project Phases

#### List Phases
- **URL**: `/phases/`
- **Method**: `GET`
- **Description**: Retrieve a list of project phases
- **Query Parameters**:
  - `search`: Search phases by name or description
  - `ordering`: Order by field (order, start_date, end_date, progress)
- **Response**: List of phases

#### Create Phase
- **URL**: `/phases/`
- **Method**: `POST`
- **Description**: Create a new project phase
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "schedule": "integer",
    "start_date": "date",
    "end_date": "date",
    "order": "integer",
    "is_active": "boolean"
  }
  ```
- **Response**: Created phase details

#### Phase Actions

##### Reorder Phases
- **URL**: `/phases/{id}/reorder/`
- **Method**: `POST`
- **Description**: Change phase order
- **Request Body**:
  ```json
  {
    "new_order": "integer"
  }
  ```

### Milestones

#### List Milestones
- **URL**: `/milestones/`
- **Method**: `GET`
- **Description**: Retrieve a list of milestones
- **Query Parameters**:
  - `search`: Search milestones by name or description
  - `ordering`: Order by field (due_date, status)
- **Response**: List of milestones

#### Create Milestone
- **URL**: `/milestones/`
- **Method**: `POST`
- **Description**: Create a new milestone
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "schedule": "integer",
    "phase": "integer",
    "due_date": "date",
    "status": "string"
  }
  ```
- **Response**: Created milestone details

#### Milestone Actions

##### Complete Milestone
- **URL**: `/milestones/{id}/complete/`
- **Method**: `POST`
- **Description**: Mark milestone as complete

##### Change Milestone Status
- **URL**: `/milestones/{id}/change_status/`
- **Method**: `POST`
- **Description**: Change milestone status
- **Request Body**:
  ```json
  {
    "status": "string"
  }
  ```

### Project Discussions

#### List Discussions
- **URL**: `/projects/{project_id}/discussions/`
- **Method**: `GET`
- **Description**: Retrieve project discussions
- **Response**: List of discussions

#### Create Discussion
- **URL**: `/projects/{project_id}/discussions/`
- **Method**: `POST`
- **Description**: Create a new discussion
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string",
    "is_active": "boolean"
  }
  ```
- **Response**: Created discussion details

### Discussion Attachments

#### List Attachments
- **URL**: `/projects/{project_id}/discussions/{discussion_id}/attachments/`
- **Method**: `GET`
- **Description**: Retrieve discussion attachments
- **Response**: List of attachments

#### Upload Attachment
- **URL**: `/projects/{project_id}/discussions/{discussion_id}/attachments/`
- **Method**: `POST`
- **Description**: Upload a file attachment
- **Request Body**: Multipart form data
  - `file`: File to upload
  - `description`: Attachment description
- **Response**: Created attachment details

### Notifications

#### List User Notifications
- **URL**: `/user-notifications/`
- **Method**: `GET`
- **Description**: Retrieve user's notifications
- **Response**: List of notifications

#### Mark Notification as Read
- **URL**: `/user-notifications/{id}/mark_read/`
- **Method**: `POST`
- **Description**: Mark a notification as read

#### Mark All Notifications as Read
- **URL**: `/user-notifications/mark_all_read/`
- **Method**: `POST`
- **Description**: Mark all notifications as read

## Error Responses

The API uses standard HTTP status codes and returns error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

Common status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Pagination

List endpoints support pagination with the following query parameters:
- `page`: Page number
- `page_size`: Number of items per page

Response format for paginated endpoints:
```json
{
  "count": "total number of items",
  "next": "URL for next page",
  "previous": "URL for previous page",
  "results": [
    // List of items
  ]
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. The current limits are:
- 1000 requests per hour per user
- 100 requests per minute per IP address

Rate limit headers are included in the response:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1516131940
``` 