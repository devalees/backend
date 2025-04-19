# Contacts API Documentation

## Base URL
All endpoints are prefixed with `/api/contacts/`

## Authentication
All endpoints require JWT authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting
Some endpoints have rate limiting applied. The response headers will include:
- `X-RateLimit-Limit`: Maximum number of requests allowed
- `X-RateLimit-Remaining`: Number of requests remaining
- `X-RateLimit-Reset`: Time when the rate limit resets

## Role-Based Access Control
All endpoints now implement Role-Based Access Control (RBAC). Users can only access:
- Resources belonging to organizations they have active roles in
- Actions their role permissions allow them to perform

## Advanced Filtering
All list endpoints now support advanced filtering capabilities using JSON-formatted filter criteria:

```
GET /api/contacts/contacts/?filters={"name__contains":"John","is_active":true}
```

### Available Filter Operators:
- `exact`: Exact match (default)
- `iexact`: Case-insensitive exact match
- `contains`: Case-sensitive contains
- `icontains`: Case-insensitive contains
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `in`: In a list of values
- `startswith`: Starts with
- `istartswith`: Case-insensitive starts with
- `endswith`: Ends with
- `iendswith`: Case-insensitive ends with

### Get Available Filters
Each resource has an endpoint to discover available filters:

```
GET /api/contacts/contacts/available_filters/
```

## Aggregation Support
All list endpoints now support data aggregation with JSON-formatted criteria:

```
GET /api/contacts/contacts/?aggregate={"count":"id","group_by":"organization"}
```

### Available Aggregation Functions:
- `count`: Count records
- `sum`: Sum field values
- `avg`: Average field values
- `min`: Minimum field value
- `max`: Maximum field value

### Get Available Aggregations
Each resource has an endpoint to discover available aggregations:

```
GET /api/contacts/contacts/available_aggregations/
```

## Available Filters and Aggregations by Model

### Contact Model

#### Available Filters
- **Text Fields**: `name`, `first_name`, `email`, `phone`
- **Date Fields**: `created_at`, `updated_at`
- **Boolean Fields**: `is_active`
- **Related Fields**:
  - `organization`: Organization name
  - `department`: Department name
  - `team`: Team name

#### Available Aggregations
- **Count Fields**: `id`
- **Group By Fields**: `organization`, `department`, `team`, `is_active`

### ContactGroup Model

#### Available Filters
- **Text Fields**: `name`, `description`
- **Date Fields**: `created_at`, `updated_at`
- **Boolean Fields**: `is_active`
- **Related Fields**:
  - `organization`: Organization name
  - `parent`: Parent group name
  - `contacts`: Contact name

#### Available Aggregations
- **Count Fields**: `id`, `contacts`
- **Group By Fields**: `organization`, `parent`, `is_active`

To get the complete and up-to-date list of available filters and aggregations for each model, use the `/available_filters/` and `/available_aggregations/` endpoints.

## Endpoints

### Contacts

#### List Contacts
- **URL**: `/contacts/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `search`: Search contacts by name or email
  - `ordering`: Order contacts by field (prefix with - for descending)
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact objects or aggregation results

#### Get Available Filters for Contacts
- **URL**: `/contacts/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Contacts
- **URL**: `/contacts/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Contact
- **URL**: `/contacts/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact object

#### Create Contact
- **URL**: `/contacts/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "email": "string",
    "phone": "string",
    "organization": "integer",
    "department": "integer",
    "team": "integer",
    "is_active": "boolean"
}
```

#### Update Contact
- **URL**: `/contacts/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Contact
- **URL**: `/contacts/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Contact
- **URL**: `/contacts/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Refresh Contact Cache
- **URL**: `/contacts/refresh_cache/`
- **Method**: `GET`
- **Auth Required**: Yes

### Contact Groups

#### List Contact Groups
- **URL**: `/contact-groups/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact group objects or aggregation results

#### Get Available Filters for Contact Groups
- **URL**: `/contact-groups/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Contact Groups
- **URL**: `/contact-groups/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Contact Group
- **URL**: `/contact-groups/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact group object

#### Create Contact Group
- **URL**: `/contact-groups/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "contact_ids": ["integer"],
    "is_active": "boolean"
}
```

#### Update Contact Group
- **URL**: `/contact-groups/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Contact Group
- **URL**: `/contact-groups/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Contact Templates

#### List Contact Templates
- **URL**: `/contact-templates/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact template objects or aggregation results

#### Get Available Filters for Contact Templates
- **URL**: `/contact-templates/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Contact Templates
- **URL**: `/contact-templates/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Contact Template
- **URL**: `/contact-templates/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact template object

#### Create Contact Template
- **URL**: `/contact-templates/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "fields": {
        "field_name": {
            "type": "string",
            "required": "boolean"
        }
    },
    "is_active": "boolean"
}
```

#### Update Contact Template
- **URL**: `/contact-templates/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Contact Template
- **URL**: `/contact-templates/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Communications

#### List Communications
- **URL**: `/communications/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `contact`: Filter by contact ID
  - `status`: Filter by status
  - `type`: Filter by communication type
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of communication objects or aggregation results

#### Get Available Filters for Communications
- **URL**: `/communications/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Communications
- **URL**: `/communications/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Communication
- **URL**: `/communications/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Communication object

#### Create Communication
- **URL**: `/communications/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "subject": "string",
    "message": "string",
    "communication_type": "string",
    "status": "string",
    "contact": "integer",
    "organization": "integer",
    "scheduled_at": "datetime",
    "is_active": "boolean",
    "metadata": "object"
}
```

#### Update Communication
- **URL**: `/communications/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Communication
- **URL**: `/communications/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Communication
- **URL**: `/communications/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Send Communication
- **URL**: `/communications/{id}/send/`
- **Method**: `POST`
- **Auth Required**: Yes

#### Schedule Communication
- **URL**: `/communications/{id}/schedule/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "scheduled_at": "datetime"
}
```

#### Cancel Communication
- **URL**: `/communications/{id}/cancel/`
- **Method**: `POST`
- **Auth Required**: Yes

### Communication Templates

#### List Communication Templates
- **URL**: `/communication-templates/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of communication template objects or aggregation results

#### Get Available Filters for Communication Templates
- **URL**: `/communication-templates/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Communication Templates
- **URL**: `/communication-templates/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Communication Template
- **URL**: `/communication-templates/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Communication template object

#### Create Communication Template
- **URL**: `/communication-templates/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "subject_template": "string",
    "message_template": "string",
    "communication_type": "string",
    "organization": "integer",
    "is_active": "boolean"
}
```

#### Update Communication Template
- **URL**: `/communication-templates/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Communication Template
- **URL**: `/communication-templates/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Create Communication from Template
- **URL**: `/communication-templates/{id}/create_communication/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "contact": "integer",
    "organization": "integer",
    "scheduled_at": "datetime",
    "metadata": "object"
}
```

### Contact Lists

#### List Contact Lists
- **URL**: `/contact-lists/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact list objects or aggregation results

#### Get Available Filters for Contact Lists
- **URL**: `/contact-lists/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Contact Lists
- **URL**: `/contact-lists/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Contact List
- **URL**: `/contact-lists/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact list object

#### Create Contact List
- **URL**: `/contact-lists/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "name": "string",
    "description": "string",
    "organization": "integer",
    "contact_ids": ["integer"],
    "is_active": "boolean",
    "metadata": "object"
}
```

#### Update Contact List
- **URL**: `/contact-lists/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Contact List
- **URL**: `/contact-lists/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Contact List
- **URL**: `/contact-lists/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes

### Contact Notes

#### List Contact Notes
- **URL**: `/contact-notes/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Query Parameters**:
  - `organization`: Filter by organization ID
  - `contact`: Filter by contact ID
  - `filters`: JSON-formatted filter criteria
  - `aggregate`: JSON-formatted aggregation criteria
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact note objects or aggregation results

#### Get Available Filters for Contact Notes
- **URL**: `/contact-notes/available_filters/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available filter fields by type

#### Get Available Aggregations for Contact Notes
- **URL**: `/contact-notes/available_aggregations/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Object with available aggregation fields by type

#### Get Contact Note
- **URL**: `/contact-notes/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact note object

#### Create Contact Note
- **URL**: `/contact-notes/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "contact": "integer",
    "organization": "integer",
    "content": "string",
    "file_attachment": "file",
    "is_private": "boolean",
    "is_active": "boolean"
}
```

#### Update Contact Note
- **URL**: `/contact-notes/{id}/`
- **Method**: `PUT`/`PATCH`
- **Auth Required**: Yes
- **Data Constraints**: Same as create

#### Delete Contact Note
- **URL**: `/contact-notes/{id}/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Hard Delete Contact Note
- **URL**: `/contact-notes/{id}/hard_delete/`
- **Method**: `DELETE`
- **Auth Required**: Yes

#### Download Note File
- **URL**: `/contact-notes/{id}/download_file/`
- **Method**: `GET`
- **Auth Required**: Yes

### Contact Note Notifications

#### List Contact Note Notifications
- **URL**: `/contact-note-notifications/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact note notification objects

#### Get Contact Note Notification
- **URL**: `/contact-note-notifications/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact note notification object

#### Create Contact Note Notification
- **URL**: `/contact-note-notifications/`
- **Method**: `POST`
- **Auth Required**: Yes
- **Data Constraints**:
```json
{
    "note": "integer",
    "user": "integer",
    "notification_type": "string",
    "message": "string",
    "is_read": "boolean",
    "metadata": "object"
}
```

#### Mark Notification as Read
- **URL**: `/contact-note-notifications/{id}/mark_read/`
- **Method**: `POST`
- **Auth Required**: Yes

#### Mark All Notifications as Read
- **URL**: `/contact-note-notifications/mark_all_read/`
- **Method**: `POST`
- **Auth Required**: Yes

#### Get Unread Notifications Count
- **URL**: `/contact-note-notifications/unread_count/`
- **Method**: `GET`
- **Auth Required**: Yes

### Contact Note Monitoring

#### List Contact Note Monitoring
- **URL**: `/contact-note-monitoring/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: List of contact note monitoring objects

#### Get Contact Note Monitoring
- **URL**: `/contact-note-monitoring/{id}/`
- **Method**: `GET`
- **Auth Required**: Yes
- **Success Response**:
  - **Code**: 200 OK
  - **Content**: Contact note monitoring object

#### Get Activity Summary
- **URL**: `/contact-note-monitoring/activity_summary/`
- **Method**: `GET`
- **Auth Required**: Yes

#### Get User Activity
- **URL**: `/contact-note-monitoring/user_activity/`
- **Method**: `GET`
- **Auth Required**: Yes

## Data Models

### Contact Object
```json
{
    "id": "integer",
    "name": "string",
    "email": "string",
    "phone": "string",
    "organization": "integer",
    "organization_name": "string",
    "department": "integer",
    "department_name": "string",
    "team": "integer",
    "team_name": "string",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Contact Group Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": "integer",
    "organization_name": "string",
    "contacts": ["Contact Object"],
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Contact Template Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": "integer",
    "organization_name": "string",
    "fields": {
        "field_name": {
            "type": "string",
            "required": "boolean"
        }
    },
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "integer",
    "created_by_name": "string",
    "updated_by": "integer",
    "updated_by_name": "string"
}
```

### Communication Object
```json
{
    "id": "integer",
    "subject": "string",
    "message": "string",
    "communication_type": "string",
    "status": "string",
    "contact": "integer",
    "contact_name": "string",
    "organization": "integer",
    "organization_name": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "scheduled_at": "datetime",
    "sent_at": "datetime",
    "created_by": "integer",
    "created_by_name": "string",
    "updated_by": "integer",
    "updated_by_name": "string",
    "is_active": "boolean",
    "metadata": "object"
}
```

### Communication Template Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "subject_template": "string",
    "message_template": "string",
    "communication_type": "string",
    "organization": "integer",
    "organization_name": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "integer",
    "created_by_name": "string",
    "updated_by": "integer",
    "updated_by_name": "string",
    "is_active": "boolean"
}
```

### Contact List Object
```json
{
    "id": "integer",
    "name": "string",
    "description": "string",
    "organization": "integer",
    "organization_name": "string",
    "contacts": ["Contact Object"],
    "is_active": "boolean",
    "metadata": "object",
    "created_at": "datetime",
    "updated_at": "datetime",
    "created_by": "integer",
    "created_by_name": "string",
    "updated_by": "integer",
    "updated_by_name": "string"
}
```

### Contact Note Object
```json
{
    "id": "integer",
    "contact": "integer",
    "contact_name": "string",
    "organization": "integer",
    "organization_name": "string",
    "content": "string",
    "created_by": "integer",
    "created_by_name": "string",
    "file_attachment": "string",
    "file_url": "string",
    "file_type": "string",
    "is_private": "boolean",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Contact Note Notification Object
```json
{
    "id": "integer",
    "note": "integer",
    "note_id": "integer",
    "user": "integer",
    "user_name": "string",
    "notification_type": "string",
    "message": "string",
    "is_read": "boolean",
    "created_at": "datetime",
    "metadata": "object"
}
```

### Contact Note Monitoring Object
```json
{
    "id": "integer",
    "note": "integer",
    "note_content": "string",
    "user": "integer",
    "user_name": "string",
    "activity_type": "string",
    "description": "string",
    "organization": "integer",
    "organization_name": "string",
    "created_at": "datetime",
    "ip_address": "string",
    "user_agent": "string",
    "metadata": "object"
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
- **Code**: 429 TOO MANY REQUESTS
  - **Content**: `{"error": "Request was throttled"}`
- **Code**: 500 INTERNAL SERVER ERROR
  - **Content**: `{"error": "Internal server error"}`

## Filtering Examples

### Basic Filtering
```
GET /api/contacts/contacts/?filters={"name__contains":"John"}
```

### Multiple Conditions
```
GET /api/contacts/contacts/?filters={"name__contains":"John","is_active":true}
```

### Filtering with Related Objects
```
GET /api/contacts/contacts/?filters={"organization__name":"Acme Corp"}
```

### Complex Date Filtering
```
GET /api/contacts/communications/?filters={"created_at__gte":"2023-01-01","created_at__lt":"2023-12-31"}
```

## Aggregation Examples

### Count Records by Organization
```
GET /api/contacts/contacts/?aggregate={"count":"id","group_by":"organization"}
```

### Multiple Aggregations
```
GET /api/contacts/contacts/?aggregate={"count":"id","group_by":["organization","is_active"]}
```

### Combining with Filters
```
GET /api/contacts/contacts/?filters={"is_active":true}&aggregate={"count":"id","group_by":"organization"}
``` 