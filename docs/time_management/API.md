# Time Management API Documentation

## Base URL
`/api/time-management/`

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Rate Limiting
Some endpoints are rate-limited. When limits are exceeded, you'll receive a 429 response:
```json
{
    "detail": "Request was throttled. Expected available in [time] seconds."
}
```

## Endpoints

### Time Categories

#### List Categories
```http
GET /categories/
```

Query Parameters:
- `search`: Search by name or description
- `ordering`: Order by name or created_at (prefix with - for descending)

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Development",
            "description": "Software development work",
            "is_billable": true,
            "color": "#4CAF50",
            "created_by": 1,
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    ]
}
```

#### Create Category
```http
POST /categories/
```

Request Body:
```json
{
    "name": "Development",
    "description": "Software development work",
    "is_billable": true,
    "color": "#4CAF50"
}
```

#### Get Category Details
```http
GET /categories/{id}/
```

#### Update Category
```http
PUT /categories/{id}/
PATCH /categories/{id}/
```

#### Delete Category
```http
DELETE /categories/{id}/
```

### Time Entries

#### List Time Entries
```http
GET /entries/
```

Query Parameters:
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `project_id`: Filter by project ID
- `search`: Search by description or project name
- `ordering`: Order by start_time, end_time, or hours (prefix with - for descending)

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "project": 1,
            "category": 1,
            "description": "Implemented user authentication",
            "start_time": "2024-03-20T09:00:00Z",
            "end_time": "2024-03-20T17:00:00Z",
            "hours": 8.00,
            "is_billable": true,
            "task": 1,
            "project_phase": 1,
            "milestone": 1,
            "created_at": "2024-03-20T17:00:00Z",
            "updated_at": "2024-03-20T17:00:00Z"
        }
    ]
}
```

#### Create Time Entry
```http
POST /entries/
```

Request Body:
```json
{
    "project": 1,
    "category": 1,
    "description": "Implemented user authentication",
    "start_time": "2024-03-20T09:00:00Z",
    "end_time": "2024-03-20T17:00:00Z",
    "is_billable": true,
    "task": 1,
    "project_phase": 1,
    "milestone": 1
}
```

#### Get Time Entry Details
```http
GET /entries/{id}/
```

#### Update Time Entry
```http
PUT /entries/{id}/
PATCH /entries/{id}/
```

#### Delete Time Entry
```http
DELETE /entries/{id}/
```

#### Get Time Entry Summary
```http
GET /entries/summary/
```

Query Parameters:
- `start_date`: Start date for summary (YYYY-MM-DD)
- `end_date`: End date for summary (YYYY-MM-DD)

Response:
```json
{
    "total_hours": 40.0,
    "billable_hours": 35.0,
    "non_billable_hours": 5.0
}
```

### Timesheets

#### List Timesheets
```http
GET /timesheets/
```

Query Parameters:
- `ordering`: Order by start_date, end_date, or status (prefix with - for descending)

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "start_date": "2024-03-01",
            "end_date": "2024-03-15",
            "status": "submitted",
            "total_hours": 80.0,
            "notes": "Completed all planned tasks",
            "submitted_at": "2024-03-15T17:00:00Z",
            "approved_at": null,
            "created_at": "2024-03-01T00:00:00Z",
            "updated_at": "2024-03-15T17:00:00Z"
        }
    ]
}
```

#### Create Timesheet
```http
POST /timesheets/
```

Request Body:
```json
{
    "start_date": "2024-03-01",
    "end_date": "2024-03-15",
    "notes": "Completed all planned tasks"
}
```

#### Get Timesheet Details
```http
GET /timesheets/{id}/
```

#### Update Timesheet
```http
PUT /timesheets/{id}/
PATCH /timesheets/{id}/
```

#### Delete Timesheet
```http
DELETE /timesheets/{id}/
```

#### Approve Timesheet
```http
POST /timesheets/{id}/approve/
```

#### Reject Timesheet
```http
POST /timesheets/{id}/reject/
```

Request Body:
```json
{
    "reason": "Missing documentation for some tasks"
}
```

### Timesheet Entries

#### List Timesheet Entries
```http
GET /timesheet-entries/
```

Query Parameters:
- `timesheet`: Filter by timesheet ID
- `ordering`: Order by date or created_at (prefix with - for descending)

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "timesheet": 1,
            "time_entry": 1,
            "date": "2024-03-20",
            "hours": 8.0,
            "category": 1,
            "description": "Implemented user authentication",
            "notes": "Completed all planned features",
            "created_at": "2024-03-20T17:00:00Z",
            "updated_at": "2024-03-20T17:00:00Z"
        }
    ]
}
```

#### Create Timesheet Entry
```http
POST /timesheet-entries/
```

Request Body:
```json
{
    "timesheet": 1,
    "time_entry": 1,
    "date": "2024-03-20",
    "hours": 8.0,
    "category": 1,
    "description": "Implemented user authentication",
    "notes": "Completed all planned features"
}
```

#### Get Timesheet Entry Details
```http
GET /timesheet-entries/{id}/
```

#### Update Timesheet Entry
```http
PUT /timesheet-entries/{id}/
PATCH /timesheet-entries/{id}/
```

#### Delete Timesheet Entry
```http
DELETE /timesheet-entries/{id}/
```

### Work Schedules

#### List Work Schedules
```http
GET /schedules/
```

Response:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": 1,
            "name": "Default Schedule",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "days_of_week": [0, 1, 2, 3, 4],
            "is_active": true,
            "created_at": "2024-03-20T00:00:00Z",
            "updated_at": "2024-03-20T00:00:00Z"
        }
    ]
}
```

#### Create Work Schedule
```http
POST /schedules/
```

Request Body:
```json
{
    "name": "Default Schedule",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true
}
```

#### Get Work Schedule Details
```http
GET /schedules/{id}/
```

#### Update Work Schedule
```http
PUT /schedules/{id}/
PATCH /schedules/{id}/
```

#### Delete Work Schedule
```http
DELETE /schedules/{id}/
```

#### Get Current Schedule
```http
GET /schedules/current/
```

Response:
```json
{
    "id": 1,
    "user": 1,
    "name": "Default Schedule",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true,
    "created_at": "2024-03-20T00:00:00Z",
    "updated_at": "2024-03-20T00:00:00Z"
}
```

## Error Responses

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

### 429 Too Many Requests
```json
{
    "detail": "Request was throttled. Expected available in [time] seconds."
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error"
}
``` 