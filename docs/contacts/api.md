# Contacts API Documentation

## Base URL
```
/api/contacts/
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Rate Limiting
Some endpoints are rate-limited to prevent abuse. When rate limits are exceeded, the API will return a 429 Too Many Requests response with headers indicating when the rate limit will reset.

## Endpoints

### 1. Contacts

#### List Contacts
**Endpoint:** `GET /contacts/`

**Query Parameters:**
- `organization`: Filter contacts by organization ID
- `search`: Search contacts by name or email
- `ordering`: Order contacts by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "organization": 1,
        "organization_name": "Example Org",
        "department": 1,
        "department_name": "Sales",
        "team": 1,
        "team_name": "Enterprise",
        "is_active": true,
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z"
    }
]
```

#### Get Contact Details
**Endpoint:** `GET /contacts/<contact_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "organization": 1,
    "organization_name": "Example Org",
    "department": 1,
    "department_name": "Sales",
    "team": 1,
    "team_name": "Enterprise",
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z"
}
```

#### Create Contact
**Endpoint:** `POST /contacts/`

**Request Body:**
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "organization": 1,
    "department": 1,
    "team": 1
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "organization": 1,
    "organization_name": "Example Org",
    "department": 1,
    "department_name": "Sales",
    "team": 1,
    "team_name": "Enterprise",
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z"
}
```

#### Update Contact
**Endpoint:** `PUT /contacts/<contact_id>/`

**Request Body:**
```json
{
    "name": "John Updated",
    "email": "john.updated@example.com",
    "phone": "+1987654321"
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "John Updated",
    "email": "john.updated@example.com",
    "phone": "+1987654321",
    "organization": 1,
    "organization_name": "Example Org",
    "department": 1,
    "department_name": "Sales",
    "team": 1,
    "team_name": "Enterprise",
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:30:00Z"
}
```

#### Delete Contact (Soft Delete)
**Endpoint:** `DELETE /contacts/<contact_id>/`

**Response:** `204 No Content`

#### Hard Delete Contact
**Endpoint:** `DELETE /contacts/<contact_id>/hard-delete/`

**Response:** `204 No Content`

#### Get Available Filters
**Endpoint:** `GET /contacts/available-filters/`

**Response:** `200 OK`
```json
{
    "filters": [
        // List of available filter fields and operators
    ]
}
```

#### Get Available Aggregations
**Endpoint:** `GET /contacts/available-aggregations/`

**Response:** `200 OK`
```json
{
    "aggregations": [
        // List of available aggregation functions
    ]
}
```

#### Refresh Cache
**Endpoint:** `GET /contacts/refresh-cache/`

**Response:** `200 OK`
```json
{
    "message": "Cache refreshed successfully"
}
```

### 2. Contact Groups

#### List Contact Groups
**Endpoint:** `GET /groups/`

**Query Parameters:**
- `organization`: Filter groups by organization ID
- `search`: Search groups by name
- `ordering`: Order groups by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "VIP Clients",
        "description": "Our most important clients",
        "organization": 1,
        "organization_name": "Example Org",
        "contacts": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            }
        ],
        "is_active": true,
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z"
    }
]
```

#### Get Contact Group Details
**Endpoint:** `GET /groups/<group_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "VIP Clients",
    "description": "Our most important clients",
    "organization": 1,
    "organization_name": "Example Org",
    "contacts": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
    ],
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z"
}
```

#### Create Contact Group
**Endpoint:** `POST /groups/`

**Request Body:**
```json
{
    "name": "VIP Clients",
    "description": "Our most important clients",
    "organization": 1,
    "contact_ids": [1, 2, 3]
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "VIP Clients",
    "description": "Our most important clients",
    "organization": 1,
    "organization_name": "Example Org",
    "contacts": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+0987654321"
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "phone": "+1122334455"
        }
    ],
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z"
}
```

#### Update Contact Group
**Endpoint:** `PUT /groups/<group_id>/`

**Request Body:**
```json
{
    "name": "Premium Clients",
    "description": "Our premium tier clients",
    "contact_ids": [1, 2, 3, 4]
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Premium Clients",
    "description": "Our premium tier clients",
    "organization": 1,
    "organization_name": "Example Org",
    "contacts": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+0987654321"
        },
        {
            "id": 3,
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "phone": "+1122334455"
        },
        {
            "id": 4,
            "name": "Alice Brown",
            "email": "alice@example.com",
            "phone": "+5566778899"
        }
    ],
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:30:00Z"
}
```

#### Delete Contact Group (Soft Delete)
**Endpoint:** `DELETE /groups/<group_id>/`

**Response:** `204 No Content`

#### Hard Delete Contact Group
**Endpoint:** `DELETE /groups/<group_id>/hard-delete/`

**Response:** `204 No Content`

#### Get Available Filters
**Endpoint:** `GET /groups/available-filters/`

**Response:** `200 OK`
```json
{
    "filters": [
        // List of available filter fields and operators
    ]
}
```

#### Get Available Aggregations
**Endpoint:** `GET /groups/available-aggregations/`

**Response:** `200 OK`
```json
{
    "aggregations": [
        // List of available aggregation functions
    ]
}
```

### 3. Contact Templates

#### List Contact Templates
**Endpoint:** `GET /templates/`

**Query Parameters:**
- `organization`: Filter templates by organization ID
- `search`: Search templates by name
- `ordering`: Order templates by field (prefix with - for descending)

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "Customer Template",
        "description": "Template for customer contacts",
        "organization": 1,
        "organization_name": "Example Org",
        "fields": {
            "company": {
                "type": "text",
                "required": true
            },
            "position": {
                "type": "text",
                "required": false
            },
            "industry": {
                "type": "select",
                "required": false,
                "options": ["Technology", "Finance", "Healthcare"]
            }
        },
        "is_active": true,
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z",
        "created_by": 1,
        "created_by_name": "admin",
        "updated_by": 1,
        "updated_by_name": "admin"
    }
]
```

#### Get Contact Template Details
**Endpoint:** `GET /templates/<template_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Customer Template",
    "description": "Template for customer contacts",
    "organization": 1,
    "organization_name": "Example Org",
    "fields": {
        "company": {
            "type": "text",
            "required": true
        },
        "position": {
            "type": "text",
            "required": false
        },
        "industry": {
            "type": "select",
            "required": false,
            "options": ["Technology", "Finance", "Healthcare"]
        }
    },
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin"
}
```

#### Create Contact Template
**Endpoint:** `POST /templates/`

**Request Body:**
```json
{
    "name": "Customer Template",
    "description": "Template for customer contacts",
    "organization": 1,
    "fields": {
        "company": {
            "type": "text",
            "required": true
        },
        "position": {
            "type": "text",
            "required": false
        },
        "industry": {
            "type": "select",
            "required": false,
            "options": ["Technology", "Finance", "Healthcare"]
        }
    }
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "Customer Template",
    "description": "Template for customer contacts",
    "organization": 1,
    "organization_name": "Example Org",
    "fields": {
        "company": {
            "type": "text",
            "required": true
        },
        "position": {
            "type": "text",
            "required": false
        },
        "industry": {
            "type": "select",
            "required": false,
            "options": ["Technology", "Finance", "Healthcare"]
        }
    },
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin"
}
```

#### Update Contact Template
**Endpoint:** `PUT /templates/<template_id>/`

**Request Body:**
```json
{
    "name": "Updated Customer Template",
    "description": "Updated template for customer contacts",
    "fields": {
        "company": {
            "type": "text",
            "required": true
        },
        "position": {
            "type": "text",
            "required": true
        },
        "industry": {
            "type": "select",
            "required": true,
            "options": ["Technology", "Finance", "Healthcare", "Education"]
        }
    }
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Updated Customer Template",
    "description": "Updated template for customer contacts",
    "organization": 1,
    "organization_name": "Example Org",
    "fields": {
        "company": {
            "type": "text",
            "required": true
        },
        "position": {
            "type": "text",
            "required": true
        },
        "industry": {
            "type": "select",
            "required": true,
            "options": ["Technology", "Finance", "Healthcare", "Education"]
        }
    },
    "is_active": true,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:30:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin"
}
```

#### Delete Contact Template
**Endpoint:** `DELETE /templates/<template_id>/`

**Response:** `204 No Content`

### 4. Communications

#### List Communications
**Endpoint:** `GET /communications/`

**Query Parameters:**
- `organization`: Filter communications by organization ID
- `contact`: Filter communications by contact ID
- `communication_type`: Filter by communication type (email, sms, call, letter, meeting, other)
- `status`: Filter by status (draft, scheduled, sending, sent, failed, cancelled)
- `search`: Search communications by subject
- `ordering`: Order communications by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "subject": "Meeting Follow-up",
        "message": "Thank you for your time today...",
        "communication_type": "email",
        "status": "sent",
        "contact": 1,
        "contact_name": "John Doe",
        "organization": 1,
        "organization_name": "Example Org",
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z",
        "scheduled_at": null,
        "sent_at": "2024-04-19T12:05:00Z",
        "created_by": 1,
        "created_by_name": "admin",
        "updated_by": 1,
        "updated_by_name": "admin",
        "is_active": true,
        "metadata": {}
    }
]
```

#### Get Communication Details
**Endpoint:** `GET /communications/<communication_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "subject": "Meeting Follow-up",
    "message": "Thank you for your time today...",
    "communication_type": "email",
    "status": "sent",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "scheduled_at": null,
    "sent_at": "2024-04-19T12:05:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {}
}
```

#### Create Communication
**Endpoint:** `POST /communications/`

**Request Body:**
```json
{
    "subject": "Meeting Follow-up",
    "message": "Thank you for your time today...",
    "communication_type": "email",
    "contact": 1,
    "organization": 1,
    "scheduled_at": "2024-04-20T10:00:00Z",
    "metadata": {
        "priority": "high"
    }
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "subject": "Meeting Follow-up",
    "message": "Thank you for your time today...",
    "communication_type": "email",
    "status": "scheduled",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "scheduled_at": "2024-04-20T10:00:00Z",
    "sent_at": null,
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {
        "priority": "high"
    }
}
```

#### Update Communication
**Endpoint:** `PUT /communications/<communication_id>/`

**Request Body:**
```json
{
    "subject": "Updated Meeting Follow-up",
    "message": "Thank you for your time today. Here are the action items...",
    "scheduled_at": "2024-04-21T10:00:00Z"
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "subject": "Updated Meeting Follow-up",
    "message": "Thank you for your time today. Here are the action items...",
    "communication_type": "email",
    "status": "scheduled",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:30:00Z",
    "scheduled_at": "2024-04-21T10:00:00Z",
    "sent_at": null,
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {
        "priority": "high"
    }
}
```

#### Delete Communication (Soft Delete)
**Endpoint:** `DELETE /communications/<communication_id>/`

**Response:** `204 No Content`

#### Hard Delete Communication
**Endpoint:** `DELETE /communications/<communication_id>/hard-delete/`

**Response:** `204 No Content`

#### Send Communication
**Endpoint:** `POST /communications/<communication_id>/send/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "subject": "Updated Meeting Follow-up",
    "message": "Thank you for your time today. Here are the action items...",
    "communication_type": "email",
    "status": "sent",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:35:00Z",
    "scheduled_at": null,
    "sent_at": "2024-04-19T12:35:00Z",
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {
        "priority": "high"
    }
}
```

#### Schedule Communication
**Endpoint:** `POST /communications/<communication_id>/schedule/`

**Request Body:**
```json
{
    "scheduled_at": "2024-04-22T09:00:00Z"
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "subject": "Updated Meeting Follow-up",
    "message": "Thank you for your time today. Here are the action items...",
    "communication_type": "email",
    "status": "scheduled",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:40:00Z",
    "scheduled_at": "2024-04-22T09:00:00Z",
    "sent_at": null,
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {
        "priority": "high"
    }
}
```

#### Cancel Communication
**Endpoint:** `POST /communications/<communication_id>/cancel/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "subject": "Updated Meeting Follow-up",
    "message": "Thank you for your time today. Here are the action items...",
    "communication_type": "email",
    "status": "cancelled",
    "contact": 1,
    "contact_name": "John Doe",
    "organization": 1,
    "organization_name": "Example Org",
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:45:00Z",
    "scheduled_at": null,
    "sent_at": null,
    "created_by": 1,
    "created_by_name": "admin",
    "updated_by": 1,
    "updated_by_name": "admin",
    "is_active": true,
    "metadata": {
        "priority": "high"
    }
}
```

#### Refresh Cache
**Endpoint:** `GET /communications/refresh-cache/`

**Response:** `200 OK`
```json
{
    "message": "Cache refreshed successfully"
}
``` 