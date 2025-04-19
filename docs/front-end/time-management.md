# Time Management API Documentation

## Overview
The Time Management API provides endpoints for managing time tracking, timesheets, work schedules, and time categories. This API is designed to help users track their time, manage work schedules, and handle timesheet submissions and approvals.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Time Categories

#### List Time Categories
```http
GET /api/time-management/categories/
```
Returns a list of all time categories.

**Response**
```json
[
  {
    "id": 1,
    "name": "Development",
    "description": "Software development tasks",
    "is_billable": true,
    "created_by": 1,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Time Category
```http
POST /api/time-management/categories/
```
Create a new time category.

**Request Body**
```json
{
  "name": "Development",
  "description": "Software development tasks",
  "is_billable": true
}
```

### Time Entries

#### List Time Entries
```http
GET /api/time-management/entries/
```
Returns a list of time entries for the authenticated user.

**Query Parameters**
- `start_date`: Filter entries from this date (YYYY-MM-DD)
- `end_date`: Filter entries until this date (YYYY-MM-DD)
- `project_id`: Filter entries by project ID

**Response**
```json
[
  {
    "id": 1,
    "user": 1,
    "project": 1,
    "category": 1,
    "description": "Feature implementation",
    "start_time": "2024-04-18T09:00:00Z",
    "end_time": "2024-04-18T17:00:00Z",
    "hours": 8.0,
    "is_billable": true,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Time Entry
```http
POST /api/time-management/entries/
```
Create a new time entry.

**Request Body**
```json
{
  "project": 1,
  "category": 1,
  "description": "Feature implementation",
  "start_time": "2024-04-18T09:00:00Z",
  "end_time": "2024-04-18T17:00:00Z",
  "is_billable": true
}
```

#### Get Time Entry Summary
```http
GET /api/time-management/entries/summary/
```
Returns a summary of time entries for the authenticated user.

**Query Parameters**
- `start_date`: Start date for summary (YYYY-MM-DD)
- `end_date`: End date for summary (YYYY-MM-DD)

**Response**
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
GET /api/time-management/timesheets/
```
Returns a list of timesheets for the authenticated user.

**Response**
```json
[
  {
    "id": 1,
    "user": 1,
    "start_date": "2024-04-01",
    "end_date": "2024-04-15",
    "status": "draft",
    "total_hours": 80.0,
    "notes": "Weekly timesheet",
    "submitted_at": null,
    "approved_at": null,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Timesheet
```http
POST /api/time-management/timesheets/
```
Create a new timesheet.

**Request Body**
```json
{
  "start_date": "2024-04-01",
  "end_date": "2024-04-15",
  "notes": "Weekly timesheet"
}
```

#### Submit Timesheet
```http
POST /api/time-management/timesheets/{id}/submit/
```
Submit a timesheet for approval.

**Response**
```json
{
  "status": "timesheet submitted"
}
```

#### Approve Timesheet
```http
POST /api/time-management/timesheets/{id}/approve/
```
Approve a submitted timesheet.

**Response**
```json
{
  "status": "timesheet approved"
}
```

#### Reject Timesheet
```http
POST /api/time-management/timesheets/{id}/reject/
```
Reject a submitted timesheet.

**Response**
```json
{
  "status": "timesheet rejected"
}
```

### Timesheet Entries

#### List Timesheet Entries
```http
GET /api/time-management/timesheet-entries/
```
Returns a list of timesheet entries for the authenticated user.

**Response**
```json
[
  {
    "id": 1,
    "timesheet": 1,
    "time_entry": 1,
    "date": "2024-04-18",
    "hours": 8.0,
    "category": 1,
    "description": "Feature implementation",
    "notes": "Completed core functionality",
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Timesheet Entry
```http
POST /api/time-management/timesheet-entries/
```
Create a new timesheet entry.

**Request Body**
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

### Work Schedules

#### List Work Schedules
```http
GET /api/time-management/schedules/
```
Returns a list of work schedules for the authenticated user.

**Response**
```json
[
  {
    "id": 1,
    "user": 1,
    "name": "Default Schedule",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "days_of_week": [0, 1, 2, 3, 4],
    "is_active": true,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Work Schedule
```http
POST /api/time-management/schedules/
```
Create a new work schedule.

**Request Body**
```json
{
  "name": "Default Schedule",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "days_of_week": [0, 1, 2, 3, 4],
  "is_active": true
}
```

#### Get Current Work Schedule
```http
GET /api/time-management/schedules/current/
```
Returns the current active work schedule for the authenticated user.

**Response**
```json
{
  "id": 1,
  "user": 1,
  "name": "Default Schedule",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "days_of_week": [0, 1, 2, 3, 4],
  "is_active": true,
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T10:00:00Z"
}
```

## Error Responses

The API uses standard HTTP status codes and returns error messages in the following format:

```json
{
  "detail": "Error message description"
}
```

Common error codes:
- 400: Bad Request - Invalid input data
- 401: Unauthorized - Missing or invalid authentication
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource not found
- 500: Internal Server Error - Server-side error

## Data Validation

### Time Entries
- End time must be after start time
- Hours are automatically calculated from start and end times
- Hours cannot exceed 24 per entry

### Timesheets
- End date must be after start date
- Only one timesheet can exist for a user within a date range
- Total hours are automatically calculated from entries

### Work Schedules
- End time must be after start time
- Days of week must be values between 0 (Monday) and 6 (Sunday)
- Only one active schedule can exist per user

## Best Practices

1. **Authentication**
   - Always include the JWT token in the Authorization header
   - Handle token expiration and refresh appropriately

2. **Time Entries**
   - Create entries as soon as possible to ensure accuracy
   - Use appropriate categories for better reporting
   - Include detailed descriptions for better tracking

3. **Timesheets**
   - Submit timesheets before the deadline
   - Review entries before submission
   - Include notes for any special circumstances

4. **Work Schedules**
   - Keep schedules up to date
   - Use descriptive names for different schedules
   - Set appropriate working hours and days 