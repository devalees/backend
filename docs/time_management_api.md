# Time Management API Documentation

## Base URL
```
/api/v1/time-management/
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Time Categories

#### List Time Categories
```http
GET /time-categories/
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
            "name": "Development",
            "description": "Software development work",
            "is_billable": true,
            "created_by": 1,
            "created_at": "2024-03-29T10:00:00Z",
            "updated_at": "2024-03-29T10:00:00Z"
        }
    ]
}
```

#### Create Time Category
```http
POST /time-categories/
```

Request:
```json
{
    "name": "Development",
    "description": "Software development work",
    "is_billable": true
}
```

Response:
```json
{
    "id": 1,
    "name": "Development",
    "description": "Software development work",
    "is_billable": true,
    "created_by": 1,
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
```

### Time Entries

#### List Time Entries
```http
GET /time-entries/
```

Query Parameters:
- `project_id`: Filter by project
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `category_id`: Filter by category

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
            "description": "Working on feature X",
            "start_time": "2024-03-29T09:00:00Z",
            "end_time": "2024-03-29T11:00:00Z",
            "hours": "2.00",
            "is_billable": true,
            "created_at": "2024-03-29T10:00:00Z",
            "updated_at": "2024-03-29T10:00:00Z"
        }
    ]
}
```

#### Create Time Entry
```http
POST /time-entries/
```

Request:
```json
{
    "user": 1,
    "project": 1,
    "category": 1,
    "description": "Working on feature X",
    "start_time": "2024-03-29T09:00:00Z",
    "end_time": "2024-03-29T11:00:00Z",
    "hours": "2.00",
    "is_billable": true
}
```

Response:
```json
{
    "id": 1,
    "user": 1,
    "project": 1,
    "category": 1,
    "description": "Working on feature X",
    "start_time": "2024-03-29T09:00:00Z",
    "end_time": "2024-03-29T11:00:00Z",
    "hours": "2.00",
    "is_billable": true,
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
```

### Timesheets

#### List Timesheets
```http
GET /timesheets/
```

Query Parameters:
- `status`: Filter by status (draft, submitted, approved, rejected)
- `start_date`: Filter by start date
- `end_date`: Filter by end date

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
            "start_date": "2024-03-25",
            "end_date": "2024-03-31",
            "status": "draft",
            "total_hours": "40.00",
            "notes": "Weekly timesheet",
            "submitted_at": null,
            "approved_at": null,
            "created_at": "2024-03-29T10:00:00Z",
            "updated_at": "2024-03-29T10:00:00Z"
        }
    ]
}
```

#### Create Timesheet
```http
POST /timesheets/
```

Request:
```json
{
    "user": 1,
    "start_date": "2024-03-25",
    "end_date": "2024-03-31",
    "status": "draft",
    "notes": "Weekly timesheet",
    "total_hours": "0.00"
}
```

Response:
```json
{
    "id": 1,
    "user": 1,
    "start_date": "2024-03-25",
    "end_date": "2024-03-31",
    "status": "draft",
    "total_hours": "0.00",
    "notes": "Weekly timesheet",
    "submitted_at": null,
    "approved_at": null,
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
```

#### Submit Timesheet
```http
POST /timesheets/{id}/submit/
```

Response:
```json
{
    "id": 1,
    "status": "submitted",
    "submitted_at": "2024-03-29T10:00:00Z"
}
```

#### Approve Timesheet
```http
POST /timesheets/{id}/approve/
```

Response:
```json
{
    "id": 1,
    "status": "approved",
    "approved_at": "2024-03-29T10:00:00Z",
    "approved_by": 2
}
```

### Timesheet Entries

#### List Timesheet Entries
```http
GET /timesheet-entries/
```

Query Parameters:
- `timesheet_id`: Filter by timesheet
- `date`: Filter by date

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
            "date": "2024-03-29",
            "hours": "8.00",
            "category": 1,
            "description": "Full day of work",
            "notes": "Completed feature X",
            "created_at": "2024-03-29T10:00:00Z",
            "updated_at": "2024-03-29T10:00:00Z"
        }
    ]
}
```

#### Create Timesheet Entry
```http
POST /timesheet-entries/
```

Request:
```json
{
    "timesheet": 1,
    "time_entry": 1,
    "date": "2024-03-29",
    "hours": "8.00",
    "category": 1,
    "description": "Full day of work",
    "notes": "Completed feature X"
}
```

Response:
```json
{
    "id": 1,
    "timesheet": 1,
    "time_entry": 1,
    "date": "2024-03-29",
    "hours": "8.00",
    "category": 1,
    "description": "Full day of work",
    "notes": "Completed feature X",
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
```

### Work Schedules

#### List Work Schedules
```http
GET /schedules/
```

Query Parameters:
- `is_active`: Filter by active status

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
            "start_time": "09:00",
            "end_time": "17:00",
            "days_of_week": [0, 1, 2, 3, 4],
            "is_active": true,
            "created_at": "2024-03-29T10:00:00Z",
            "updated_at": "2024-03-29T10:00:00Z"
        }
    ]
}
```

#### Create Work Schedule
```http
POST /schedules/
```

Request:
```json
{
    "user": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true
}
```

Response:
```json
{
    "id": 1,
    "user": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true,
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
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
    "start_time": "09:00",
    "end_time": "17:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true,
    "created_at": "2024-03-29T10:00:00Z",
    "updated_at": "2024-03-29T10:00:00Z"
}
```

## Error Responses

### Validation Error
```json
{
    "field_name": [
        "Error message"
    ]
}
```

### Not Found Error
```json
{
    "detail": "Not found."
}
```

### Permission Error
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Authentication Error
```json
{
    "detail": "Authentication credentials were not provided."
}
``` 