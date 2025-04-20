# Entity API Documentation

## Base URL
All endpoints are prefixed with `/api/v1/entity/`

## Authentication
All endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Role-Based Access Control
All endpoints implement Role-Based Access Control (RBAC). Users can only access:
- Resources belonging to organizations they have active roles in
- Actions their role permissions allow them to perform

## Endpoints

### Organizations

#### List Organizations
- **URL**: `/organizations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `search`: Search organizations by name
  - `ordering`: Order organizations by field (prefix with - for descending)
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of organization objects
- **Note**: Users can only see organizations they are members of

#### Get Organization
- **URL**: `/organizations/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Organization object

#### Create Organization
- **URL**: `/organizations/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "is_active": "boolean"
}
```

#### Update Organization
- **URL**: `/organizations/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Organization
- **URL**: `/organizations/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Organization
- **URL**: `/organizations/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Note**: This permanently deletes the organization and all its departments

#### Get Organization Departments
- **URL**: `/organizations/{id}/department/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of department objects

#### Get Organization Team Members
- **URL**: `/organizations/{id}/team_member/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team member objects

#### Get Organization Analytics
- **URL**: `/organizations/{id}/analytics/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "total_departments": "integer",
    "total_teams": "integer",
    "total_members": "integer"
}
```

#### Get Organization Activity
- **URL**: `/organizations/{id}/activity/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "recent_activities": "integer",
    "engagement_metrics": {
        "active_members": "integer",
        "total_members": "integer",
        "engagement_rate": "float"
    }
}
```

#### Get Organization Performance
- **URL**: `/organizations/{id}/performance/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "team_performance": [
        {
            "name": "string",
            "member_count": "integer"
        }
    ],
    "department_performance": [
        {
            "name": "string",
            "team_count": "integer",
            "member_count": "integer"
        }
    ],
    "member_contributions": [
        {
            "user__username": "string",
            "teams_count": "integer"
        }
    ]
}
```

#### Get Organization Growth
- **URL**: `/organizations/{id}/growth/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
```json
{
    "member_growth": {
        "new_members": "integer",
        "total_members": "integer"
    },
    "team_growth": {
        "new_teams": "integer",
        "total_teams": "integer"
    },
    "department_growth": {
        "new_departments": "integer",
        "total_departments": "integer"
    }
}
```

### Departments

#### List Departments
- **URL**: `/departments/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `parent`: Filter by parent department ID
  - `search`: Search departments by name
  - `ordering`: Order departments by field (prefix with - for descending)
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of department objects

#### Get Department
- **URL**: `/departments/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Department object

#### Create Department
- **URL**: `/departments/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "parent": "integer",
    "is_active": "boolean"
}
```

#### Update Department
- **URL**: `/departments/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Department
- **URL**: `/departments/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Department
- **URL**: `/departments/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Note**: This permanently deletes the department and all its teams

#### Get Department Teams
- **URL**: `/departments/{id}/team/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team objects

#### Get Department Team Members
- **URL**: `/departments/{id}/team_member/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team member objects

#### Get Child Departments
- **URL**: `/departments/{id}/child_department/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of department objects

### Teams

#### List Teams
- **URL**: `/teams/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `department`: Filter by department ID
  - `search`: Search teams by name
  - `ordering`: Order teams by field (prefix with - for descending)
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team objects

#### Get Team
- **URL**: `/teams/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Team object

#### Create Team
- **URL**: `/teams/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "department": "integer",
    "is_active": "boolean"
}
```

#### Update Team
- **URL**: `/teams/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Team
- **URL**: `/teams/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Team
- **URL**: `/teams/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Note**: This permanently deletes the team and all its members

#### Get Team Members
- **URL**: `/teams/{id}/team_member/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team member objects

### Team Members

#### List Team Members
- **URL**: `/team-members/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `team`: Filter by team ID
  - `user`: Filter by user ID
  - `search`: Search team members by username
  - `ordering`: Order team members by field (prefix with - for descending)
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of team member objects

#### Get Team Member
- **URL**: `/team-members/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Team member object

#### Create Team Member
- **URL**: `/team-members/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "user_id": "integer",
    "team": "integer",
    "role": "string",
    "is_active": "boolean"
}
```
- **Note**: The `role` field accepts one of the following values: "admin", "member", "viewer"

#### Update Team Member
- **URL**: `/team-members/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Team Member
- **URL**: `/team-members/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Team Member
- **URL**: `/team-members/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Note**: This permanently deletes the team member

### Organization Settings

#### List Organization Settings
- **URL**: `/organization-settings/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `ordering`: Order settings by field (prefix with - for descending)
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of organization settings objects

#### Get Organization Settings
- **URL**: `/organization-settings/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Organization settings object

#### Create Organization Settings
- **URL**: `/organization-settings/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "organization": "integer",
    "timezone": "string",
    "date_format": "string",
    "time_format": "string",
    "language": "string",
    "notification_preferences": {
        "email": "boolean",
        "push": "boolean",
        "slack": "boolean"
    }
}
```
- **Validation Rules**:
  - `timezone`: Must be a valid timezone from the pytz library
  - `time_format`: Must be either "12h" or "24h"
  - `language`: Must be a valid language code (e.g., "en", "es", "fr")

#### Update Organization Settings
- **URL**: `/organization-settings/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Organization Settings
- **URL**: `/organization-settings/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Organization Settings
- **URL**: `/organization-settings/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes
- **Note**: This permanently deletes the organization settings

#### Get Settings by Organization
- **URL**: `/organization-settings/get_by_organization/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Organization ID
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Organization settings object

## Data Models

### Organization Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "status": "string",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```
- **Note**: The `status` field can be one of: "active", "inactive", "suspended"

### Department Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": "integer",
    "organization_name": "string",
    "parent": "integer",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Team Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "department": "integer",
    "department_name": "string",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Team Member Object
```json
{
    "id": "integer",
    "user": {
        "id": "integer",
        "username": "string",
        "email": "string",
        "first_name": "string",
        "last_name": "string"
    },
    "user_id": "integer",
    "team": "integer",
    "team_name": "string",
    "role": "string",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```
- **Note**: The `role` field can be one of: "admin", "member", "viewer"

### Organization Settings Object
```json
{
    "id": "integer",
    "organization": "integer",
    "timezone": "string",
    "date_format": "string",
    "time_format": "string",
    "language": "string",
    "notification_preferences": {
        "email": "boolean",
        "push": "boolean",
        "slack": "boolean"
    },
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Error Responses

All endpoints may return the following error responses:

- **Code**: 400 BAD REQUEST
  - **Content**: `{"error": "Error message"}`
- **Code**: 401 UNAUTHORIZED
  - **Content**: `{"error": "Authentication credentials were not provided"}`
- **Code**: 403 FORBIDDEN
  - **Content**: One of the following:
    - `{"error": "You do not have permission to perform this action"}`
    - `{"error": "You do not have the required role to access this resource"}`
    - `{"error": "Your role does not have permission for this action"}`
    - `{"error": "You can only access resources in organizations you are a member of"}`
- **Code**: 404 NOT FOUND
  - **Content**: `{"error": "Not found"}`
- **Code**: 500 INTERNAL SERVER ERROR
  - **Content**: `{"error": "Internal server error"}`

## Pagination

All list endpoints support pagination with the following query parameters:
- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 10, max: 100)

Example response with pagination:
```json
{
    "count": 100,
    "next": "http://api.example.com/api/v1/entity/organizations/?page=3",
    "previous": "http://api.example.com/api/v1/entity/organizations/?page=1",
    "results": [
        // List of objects
    ]
}
``` 