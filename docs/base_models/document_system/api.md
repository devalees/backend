# Documents API Documentation

## Base URL
```
/api/documents/
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Documents

#### List Documents
**Endpoint:** `GET /documents/`

**Query Parameters:**
- `organization`: Filter documents by organization ID
- `search`: Search documents by title or description
- `ordering`: Order documents by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "title": "Project Proposal",
        "description": "Initial project proposal document",
        "status": "draft",
        "file": "documents/2024/04/19/proposal.pdf",
        "user": 1,
        "user_name": "john.doe",
        "classification": 1,
        "classification_name": "Proposals",
        "tags": [
            {
                "id": 1,
                "name": "Important",
                "description": "High priority documents",
                "color": "#FF0000"
            }
        ],
        "is_deleted": false,
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z",
        "organization": 1
    }
]
```

#### Get Document Details
**Endpoint:** `GET /documents/<document_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "title": "Project Proposal",
    "description": "Initial project proposal document",
    "status": "draft",
    "file": "documents/2024/04/19/proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "classification": 1,
    "classification_name": "Proposals",
    "tags": [
        {
            "id": 1,
            "name": "Important",
            "description": "High priority documents",
            "color": "#FF0000"
        }
    ],
    "is_deleted": false,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "organization": 1
}
```

#### Create Document
**Endpoint:** `POST /documents/`

**Request Body:**
```json
{
    "title": "Project Proposal",
    "description": "Initial project proposal document",
    "status": "draft",
    "file": "<file_data>",
    "user": 1,
    "classification": 1,
    "tags": [1]
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "title": "Project Proposal",
    "description": "Initial project proposal document",
    "status": "draft",
    "file": "documents/2024/04/19/proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "classification": 1,
    "classification_name": "Proposals",
    "tags": [
        {
            "id": 1,
            "name": "Important",
            "description": "High priority documents",
            "color": "#FF0000"
        }
    ],
    "is_deleted": false,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "organization": 1
}
```

#### Update Document
**Endpoint:** `PUT /documents/<document_id>/`

**Request Body:**
```json
{
    "title": "Updated Project Proposal",
    "description": "Updated project proposal document",
    "status": "review",
    "classification": 2,
    "tags": [1, 2]
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "title": "Updated Project Proposal",
    "description": "Updated project proposal document",
    "status": "review",
    "file": "documents/2024/04/19/proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "classification": 2,
    "classification_name": "Active Projects",
    "tags": [
        {
            "id": 1,
            "name": "Important",
            "description": "High priority documents",
            "color": "#FF0000"
        },
        {
            "id": 2,
            "name": "In Review",
            "description": "Documents under review",
            "color": "#FFA500"
        }
    ],
    "is_deleted": false,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:30:00Z",
    "organization": 1
}
```

#### Delete Document (Soft Delete)
**Endpoint:** `DELETE /documents/<document_id>/`

**Response:** `204 No Content`

#### Filter Documents
**Endpoint:** `POST /documents/filter/`

**Request Body:**
```json
{
    "title": "Report",
    "status": "approved",
    "is_deleted": false
}
```

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "title": "Monthly Report",
        "status": "approved",
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z",
        "user": "john.doe",
        "classification": "Reports"
    }
]
```

#### Aggregate Documents
**Endpoint:** `POST /documents/aggregate/`

**Request Body:**
```json
{
    "aggregations": {
        "id": "count"
    },
    "group_by": ["status"]
}
```

**Response:** `200 OK`
```json
{
    "results": [
        {
            "status": "draft",
            "count": 5
        },
        {
            "status": "review",
            "count": 3
        },
        {
            "status": "approved",
            "count": 10
        }
    ]
}
```

#### Get Document Status Counts
**Endpoint:** `GET /documents/status_counts/`

**Response:** `200 OK`
```json
{
    "draft": 5,
    "review": 3,
    "approved": 10,
    "archived": 2
}
```

#### Get User Documents
**Endpoint:** `GET /documents/user_documents/`

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "title": "Project Proposal",
        "status": "draft",
        "created_at": "2024-04-19T12:00:00Z"
    }
]
```

### 2. Document Versions

#### List Document Versions
**Endpoint:** `GET /versions/`

**Query Parameters:**
- `organization`: Filter versions by organization ID
- `document`: Filter versions by document ID
- `search`: Search versions by comment or branch name
- `ordering`: Order versions by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "document": 1,
        "document_title": "Project Proposal",
        "version_number": 1,
        "file": "documents/versions/2024/04/19/v1_proposal.pdf",
        "user": 1,
        "user_name": "john.doe",
        "comment": "Initial version",
        "is_current": true,
        "branch_name": "main",
        "parent_version": null,
        "merged_to": null,
        "created_at": "2024-04-19T12:00:00Z",
        "updated_at": "2024-04-19T12:00:00Z",
        "organization": 1
    }
]
```

#### Get Document Version Details
**Endpoint:** `GET /versions/<version_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "document": 1,
    "document_title": "Project Proposal",
    "version_number": 1,
    "file": "documents/versions/2024/04/19/v1_proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "comment": "Initial version",
    "is_current": true,
    "branch_name": "main",
    "parent_version": null,
    "merged_to": null,
    "created_at": "2024-04-19T12:00:00Z",
    "updated_at": "2024-04-19T12:00:00Z",
    "organization": 1
}
```

#### Create Document Version
**Endpoint:** `POST /versions/`

**Request Body:**
```json
{
    "document": 1,
    "file": "<file_data>",
    "user": 1,
    "comment": "Updated with new sections",
    "branch_name": "main"
}
```

**Response:** `201 Created`
```json
{
    "id": 2,
    "document": 1,
    "document_title": "Project Proposal",
    "version_number": 2,
    "file": "documents/versions/2024/04/19/v2_proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "comment": "Updated with new sections",
    "is_current": true,
    "branch_name": "main",
    "parent_version": 1,
    "merged_to": null,
    "created_at": "2024-04-19T12:30:00Z",
    "updated_at": "2024-04-19T12:30:00Z",
    "organization": 1
}
```

#### Update Document Version
**Endpoint:** `PUT /versions/<version_id>/`

**Request Body:**
```json
{
    "comment": "Updated comment",
    "is_current": false
}
```

**Response:** `200 OK`
```json
{
    "id": 2,
    "document": 1,
    "document_title": "Project Proposal",
    "version_number": 2,
    "file": "documents/versions/2024/04/19/v2_proposal.pdf",
    "user": 1,
    "user_name": "john.doe",
    "comment": "Updated comment",
    "is_current": false,
    "branch_name": "main",
    "parent_version": 1,
    "merged_to": null,
    "created_at": "2024-04-19T12:30:00Z",
    "updated_at": "2024-04-19T12:35:00Z",
    "organization": 1
}
```

#### Delete Document Version
**Endpoint:** `DELETE /versions/<version_id>/`

**Response:** `204 No Content`

#### Filter Document Versions
**Endpoint:** `POST /versions/filter/`

**Request Body:**
```json
{
    "document": 1,
    "is_current": true,
    "branch_name": "main"
}
```

**Response:** `200 OK`
```json
[
    {
        "id": 2,
        "document": 1,
        "document_title": "Project Proposal",
        "version_number": 2,
        "created_at": "2024-04-19T12:30:00Z",
        "user": "john.doe",
        "is_current": true,
        "branch_name": "main"
    }
]
```

#### Aggregate Document Versions
**Endpoint:** `POST /versions/aggregate/`

**Request Body:**
```json
{
    "aggregations": {
        "id": "count",
        "version_number": "max"
    },
    "group_by": ["document"]
}
```

**Response:** `200 OK`
```json
{
    "results": [
        {
            "document": 1,
            "count": 3,
            "max_version_number": 3
        },
        {
            "document": 2,
            "count": 2,
            "max_version_number": 2
        }
    ]
}
```

#### Get Version Counts
**Endpoint:** `GET /versions/version_counts/`

**Response:** `200 OK`
```json
{
    "1": 5,
    "2": 3,
    "3": 1
}
```

### 3. Document Classifications

#### List Document Classifications
**Endpoint:** `GET /classifications/`

**Query Parameters:**
- `organization`: Filter classifications by organization ID
- `search`: Search classifications by name or description
- `ordering`: Order classifications by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "Proposals",
        "description": "Project proposals and related documents",
        "parent": null,
        "parent_name": null,
        "organization": 1
    }
]
```

#### Get Document Classification Details
**Endpoint:** `GET /classifications/<classification_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Proposals",
    "description": "Project proposals and related documents",
    "parent": null,
    "parent_name": null,
    "organization": 1
}
```

#### Create Document Classification
**Endpoint:** `POST /classifications/`

**Request Body:**
```json
{
    "name": "Proposals",
    "description": "Project proposals and related documents",
    "parent": null
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "Proposals",
    "description": "Project proposals and related documents",
    "parent": null,
    "parent_name": null,
    "organization": 1
}
```

#### Update Document Classification
**Endpoint:** `PUT /classifications/<classification_id>/`

**Request Body:**
```json
{
    "name": "Updated Proposals",
    "description": "Updated description for proposals",
    "parent": 2
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Updated Proposals",
    "description": "Updated description for proposals",
    "parent": 2,
    "parent_name": "Projects",
    "organization": 1
}
```

#### Delete Document Classification
**Endpoint:** `DELETE /classifications/<classification_id>/`

**Response:** `204 No Content`

#### Filter Document Classifications
**Endpoint:** `POST /classifications/filter/`

**Request Body:**
```json
{
    "name": "Proposals",
    "parent": null
}
```

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "Proposals",
        "description": "Project proposals and related documents",
        "parent": null,
        "parent_name": null
    }
]
```

#### Aggregate Document Classifications
**Endpoint:** `POST /classifications/aggregate/`

**Request Body:**
```json
{
    "aggregations": {
        "id": "count"
    },
    "group_by": ["parent"]
}
```

**Response:** `200 OK`
```json
{
    "results": [
        {
            "parent": null,
            "count": 3
        },
        {
            "parent": 1,
            "count": 2
        }
    ]
}
```

### 4. Document Tags

#### List Document Tags
**Endpoint:** `GET /tags/`

**Query Parameters:**
- `organization`: Filter tags by organization ID
- `search`: Search tags by name or description
- `ordering`: Order tags by field (prefix with - for descending)
- `filters`: JSON string of filter criteria
- `aggregate`: JSON string of aggregation criteria

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "Important",
        "description": "High priority documents",
        "color": "#FF0000",
        "organization": 1
    }
]
```

#### Get Document Tag Details
**Endpoint:** `GET /tags/<tag_id>/`

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Important",
    "description": "High priority documents",
    "color": "#FF0000",
    "organization": 1
}
```

#### Create Document Tag
**Endpoint:** `POST /tags/`

**Request Body:**
```json
{
    "name": "Important",
    "description": "High priority documents",
    "color": "#FF0000"
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "Important",
    "description": "High priority documents",
    "color": "#FF0000",
    "organization": 1
}
```

#### Update Document Tag
**Endpoint:** `PUT /tags/<tag_id>/`

**Request Body:**
```json
{
    "name": "Critical",
    "description": "Critical priority documents",
    "color": "#FF0000"
}
```

**Response:** `200 OK`
```json
{
    "id": 1,
    "name": "Critical",
    "description": "Critical priority documents",
    "color": "#FF0000",
    "organization": 1
}
```

#### Delete Document Tag
**Endpoint:** `DELETE /tags/<tag_id>/`

**Response:** `204 No Content`

#### Filter Document Tags
**Endpoint:** `POST /tags/filter/`

**Request Body:**
```json
{
    "name": "Important",
    "color": "#FF0000"
}
```

**Response:** `200 OK`
```json
[
    {
        "id": 1,
        "name": "Important",
        "description": "High priority documents",
        "color": "#FF0000"
    }
]
```

#### Aggregate Document Tags
**Endpoint:** `POST /tags/aggregate/`

**Request Body:**
```json
{
    "aggregations": {
        "id": "count"
    }
}
```

**Response:** `200 OK`
```json
{
    "results": [
        {
            "count": 5
        }
    ]
}
``` 