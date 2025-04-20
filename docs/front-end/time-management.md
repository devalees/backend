# Time Management API Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/time-management/`

## Authentication
All endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Time Categories

#### List Time Categories
- **URL**: `/categories/`
- **Method**: `GET`
- **Query Parameters**:
  - `search`: Search in name and description
  - `ordering`: Sort by field (e.g., name, created_at)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of time categories with pagination

#### Get Time Category
- **URL**: `/categories/{id}/`
- **Method**: `GET`
- **Response**: Time category details

#### Create Time Category
- **URL**: `/categories/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "name": "Development",
  "description": "Software development tasks",
  "is_billable": true,
  "color": "#3498db"
}
```
- **Response**: Created time category details

#### Update Time Category
- **URL**: `/categories/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Time Category
- **Response**: Updated time category details

#### Delete Time Category
- **URL**: `/categories/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

### Time Entries

#### List Time Entries
- **URL**: `/entries/`
- **Method**: `GET`
- **Query Parameters**:
  - `start_date`: Filter entries from this date (YYYY-MM-DD)
  - `end_date`: Filter entries until this date (YYYY-MM-DD)
  - `project_id`: Filter entries by project ID
  - `search`: Search in description and project name
  - `ordering`: Sort by field (e.g., start_time, end_time, hours)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of time entries with pagination

#### Get Time Entry
- **URL**: `/entries/{id}/`
- **Method**: `GET`
- **Response**: Time entry details

#### Create Time Entry
- **URL**: `/entries/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "project": 1,
  "category": 1,
  "description": "Feature implementation",
  "start_time": "2024-04-18T09:00:00Z",
  "end_time": "2024-04-18T17:00:00Z",
  "is_billable": true,
  "task": 1,
  "project_phase": 1,
  "milestone": 1
}
```
- **Response**: Created time entry details

#### Update Time Entry
- **URL**: `/entries/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Time Entry
- **Response**: Updated time entry details

#### Delete Time Entry
- **URL**: `/entries/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Time Entry Actions
- **Get Time Entry Summary**
  - **URL**: `/entries/summary/`
  - **Method**: `GET`
  - **Query Parameters**:
    - `start_date`: Start date for summary (YYYY-MM-DD)
    - `end_date`: End date for summary (YYYY-MM-DD)
  - **Response**: Summary of time entries
  ```json
  {
    "total_hours": 40.0,
    "billable_hours": 35.0,
    "non_billable_hours": 5.0
  }
  ```

### Timesheets

#### List Timesheets
- **URL**: `/timesheets/`
- **Method**: `GET`
- **Query Parameters**:
  - `ordering`: Sort by field (e.g., start_date, end_date, status)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of timesheets with pagination

#### Get Timesheet
- **URL**: `/timesheets/{id}/`
- **Method**: `GET`
- **Response**: Timesheet details

#### Create Timesheet
- **URL**: `/timesheets/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "start_date": "2024-04-01",
  "end_date": "2024-04-15",
  "notes": "Weekly timesheet"
}
```
- **Response**: Created timesheet details

#### Update Timesheet
- **URL**: `/timesheets/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Timesheet
- **Response**: Updated timesheet details

#### Delete Timesheet
- **URL**: `/timesheets/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Timesheet Actions
- **Submit Timesheet**
  - **URL**: `/timesheets/{id}/submit/`
  - **Method**: `POST`
  - **Response**: Submission status
  ```json
  {
    "status": "timesheet submitted"
  }
  ```

- **Approve Timesheet**
  - **URL**: `/timesheets/{id}/approve/`
  - **Method**: `POST`
  - **Response**: Approval status
  ```json
  {
    "status": "timesheet approved"
  }
  ```

- **Reject Timesheet**
  - **URL**: `/timesheets/{id}/reject/`
  - **Method**: `POST`
  - **Response**: Rejection status
  ```json
  {
    "status": "timesheet rejected"
  }
  ```

### Timesheet Entries

#### List Timesheet Entries
- **URL**: `/timesheet-entries/`
- **Method**: `GET`
- **Response**: List of timesheet entries with pagination

#### Get Timesheet Entry
- **URL**: `/timesheet-entries/{id}/`
- **Method**: `GET`
- **Response**: Timesheet entry details

#### Create Timesheet Entry
- **URL**: `/timesheet-entries/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "timesheet": 1,
  "time_entry": 1,
  "date": "2024-04-18",
  "hours": 8.0,
  "category": 1,
  "description": "Feature implementation",
  "notes": "Completed core functionality"
}
```
- **Response**: Created timesheet entry details

#### Update Timesheet Entry
- **URL**: `/timesheet-entries/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Timesheet Entry
- **Response**: Updated timesheet entry details

#### Delete Timesheet Entry
- **URL**: `/timesheet-entries/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

### Work Schedules

#### List Work Schedules
- **URL**: `/schedules/`
- **Method**: `GET`
- **Response**: List of work schedules with pagination

#### Get Work Schedule
- **URL**: `/schedules/{id}/`
- **Method**: `GET`
- **Response**: Work schedule details

#### Create Work Schedule
- **URL**: `/schedules/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "name": "Default Schedule",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "days_of_week": [0, 1, 2, 3, 4],
  "is_active": true
}
```
- **Response**: Created work schedule details

#### Update Work Schedule
- **URL**: `/schedules/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Work Schedule
- **Response**: Updated work schedule details

#### Delete Work Schedule
- **URL**: `/schedules/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Work Schedule Actions
- **Get Current Work Schedule**
  - **URL**: `/schedules/current/`
  - **Method**: `GET`
  - **Response**: Current active work schedule details

## Data Models

### Time Category Object
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "is_billable": "boolean",
  "color": "string",
  "created_by": "integer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Time Entry Object
```json
{
  "id": "integer",
  "user": "integer",
  "project": "integer",
  "category": "integer",
  "description": "string",
  "start_time": "datetime",
  "end_time": "datetime",
  "hours": "float",
  "is_billable": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "task": "integer",
  "project_phase": "integer",
  "milestone": "integer"
}
```

### Timesheet Object
```json
{
  "id": "integer",
  "user": "integer",
  "start_date": "date",
  "end_date": "date",
  "status": "string",
  "total_hours": "decimal",
  "notes": "string",
  "submitted_at": "datetime",
  "approved_at": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Timesheet Entry Object
```json
{
  "id": "integer",
  "timesheet": "integer",
  "time_entry": "integer",
  "date": "date",
  "hours": "float",
  "category": "integer",
  "description": "string",
  "notes": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Work Schedule Object
```json
{
  "id": "integer",
  "user": "integer",
  "name": "string",
  "start_time": "time",
  "end_time": "time",
  "days_of_week": "array",
  "is_active": "boolean",
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