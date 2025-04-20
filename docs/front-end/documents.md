# Document Management API Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/documents/`

## Authentication
All endpoints require JWT token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Documents

#### List Documents
- **URL**: `/documents/`
- **Method**: `GET`
- **Query Parameters**:
  - `status`: Filter by document status (draft, review, approved, archived)
  - `classification`: Filter by classification ID
  - `tags`: Filter by tag IDs (comma-separated)
  - `search`: Search in document title and description
  - `ordering`: Sort by field (e.g., title, created_at, updated_at)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of documents with pagination

#### Get Document
- **URL**: `/documents/{id}/`
- **Method**: `GET`
- **Response**: Document details

#### Create Document
- **URL**: `/documents/`
- **Method**: `POST`
- **Request Body (multipart/form-data)**:
```
title: Project Proposal
description: Initial project proposal document
status: draft
file: [file upload]
classification: 1
tags: [1, 2]
```
- **Response**: Created document details

#### Update Document
- **URL**: `/documents/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body (multipart/form-data)**:
```
title: Updated Project Proposal
description: Updated project proposal document
status: review
file: [file upload]
classification: 2
tags: [1, 3]
```
- **Response**: Updated document details

#### Delete Document
- **URL**: `/documents/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Document Actions
- **Filter Documents**
  - **URL**: `/documents/filter/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "title": "Report",
    "status": "approved",
    "is_deleted": false
  }
  ```
  - **Response**: Filtered document results

- **Aggregate Documents**
  - **URL**: `/documents/aggregate/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "aggregations": {
      "id": "count"
    },
    "group_by": ["status"]
  }
  ```
  - **Response**: Aggregation results

- **Get Status Counts**
  - **URL**: `/documents/status_counts/`
  - **Method**: `GET`
  - **Response**: Document counts by status

- **Get User Documents**
  - **URL**: `/documents/user_documents/`
  - **Method**: `GET`
  - **Response**: Documents belonging to the authenticated user

### Document Versions

#### List Document Versions
- **URL**: `/versions/`
- **Method**: `GET`
- **Query Parameters**:
  - `document`: Filter by document ID
  - `is_current`: Filter by current status
  - `branch_name`: Filter by branch name
  - `user`: Filter by user ID
  - `ordering`: Sort by field (e.g., version_number, created_at)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of document versions with pagination

#### Get Document Version
- **URL**: `/versions/{id}/`
- **Method**: `GET`
- **Response**: Document version details

#### Create Document Version
- **URL**: `/versions/`
- **Method**: `POST`
- **Request Body (multipart/form-data)**:
```
document: 1
file: [file upload]
comment: Updated with feedback
branch_name: main
```
- **Response**: Created document version details

#### Update Document Version
- **URL**: `/versions/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body (multipart/form-data)**:
```
comment: Updated comment
is_current: true
```
- **Response**: Updated document version details

#### Delete Document Version
- **URL**: `/versions/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Version Actions
- **Filter Versions**
  - **URL**: `/versions/filter/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "document": 1,
    "is_current": true,
    "branch_name": "main"
  }
  ```
  - **Response**: Filtered version results

- **Aggregate Versions**
  - **URL**: `/versions/aggregate/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "aggregations": {
      "id": "count",
      "version_number": "max"
    },
    "group_by": ["document", "branch_name"]
  }
  ```
  - **Response**: Aggregation results

- **Get Version Counts**
  - **URL**: `/versions/version_counts/`
  - **Method**: `GET`
  - **Response**: Version counts by document

- **Create Branch**
  - **URL**: `/versions/{id}/create_branch/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "branch_name": "feature-branch",
    "comment": "Creating feature branch"
  }
  ```
  - **Response**: Created branch details

- **Merge Branch**
  - **URL**: `/versions/{id}/merge_to/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "target_version_id": 2,
    "comment": "Merging feature branch into main"
  }
  ```
  - **Response**: Merged version details

- **Compare Versions**
  - **URL**: `/versions/compare/`
  - **Method**: `GET`
  - **Query Parameters**:
    - `version1`: First version ID
    - `version2`: Second version ID
  - **Response**: Comparison results

- **Restore Version**
  - **URL**: `/versions/{id}/restore/`
  - **Method**: `POST`
  - **Response**: Restored document details

### Document Classifications

#### List Classifications
- **URL**: `/classifications/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by classification name
  - `parent`: Filter by parent classification ID
  - `ordering`: Sort by field (e.g., name)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of classifications with pagination

#### Get Classification
- **URL**: `/classifications/{id}/`
- **Method**: `GET`
- **Response**: Classification details

#### Create Classification
- **URL**: `/classifications/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "name": "Technical Specifications",
  "description": "Technical specification documents",
  "parent": 1
}
```
- **Response**: Created classification details

#### Update Classification
- **URL**: `/classifications/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Classification
- **Response**: Updated classification details

#### Delete Classification
- **URL**: `/classifications/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Classification Actions
- **Filter Classifications**
  - **URL**: `/classifications/filter/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "name": "Technical",
    "parent": 1
  }
  ```
  - **Response**: Filtered classification results

- **Aggregate Classifications**
  - **URL**: `/classifications/aggregate/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "aggregations": {
      "id": "count"
    },
    "group_by": ["parent"]
  }
  ```
  - **Response**: Aggregation results

### Document Tags

#### List Tags
- **URL**: `/tags/`
- **Method**: `GET`
- **Query Parameters**:
  - `name`: Filter by tag name
  - `ordering`: Sort by field (e.g., name)
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
- **Response**: List of tags with pagination

#### Get Tag
- **URL**: `/tags/{id}/`
- **Method**: `GET`
- **Response**: Tag details

#### Create Tag
- **URL**: `/tags/`
- **Method**: `POST`
- **Request Body**:
```json
{
  "name": "Important",
  "description": "Important documents",
  "color": "#FF0000"
}
```
- **Response**: Created tag details

#### Update Tag
- **URL**: `/tags/{id}/`
- **Method**: `PUT/PATCH`
- **Request Body**: Same as Create Tag
- **Response**: Updated tag details

#### Delete Tag
- **URL**: `/tags/{id}/`
- **Method**: `DELETE`
- **Response**: 204 No Content

#### Tag Actions
- **Filter Tags**
  - **URL**: `/tags/filter/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "name": "Important"
  }
  ```
  - **Response**: Filtered tag results

- **Aggregate Tags**
  - **URL**: `/tags/aggregate/`
  - **Method**: `POST`
  - **Request Body**:
  ```json
  {
    "aggregations": {
      "id": "count"
    }
  }
  ```
  - **Response**: Aggregation results

## Data Models

### Document Object
```json
{
  "id": "integer",
  "title": "string",
  "description": "string",
  "status": "string",
  "file": "string (URL)",
  "user": "integer",
  "user_name": "string",
  "classification": "integer",
  "classification_name": "string",
  "tags": [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "color": "string"
    }
  ],
  "is_deleted": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "organization": "integer"
}
```

### Document Version Object
```json
{
  "id": "integer",
  "document": "integer",
  "document_title": "string",
  "version_number": "integer",
  "file": "string (URL)",
  "user": "integer",
  "user_name": "string",
  "comment": "string",
  "is_current": "boolean",
  "branch_name": "string",
  "parent_version": "integer",
  "merged_to": "integer",
  "created_at": "datetime",
  "updated_at": "datetime",
  "organization": "integer"
}
```

### Document Classification Object
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "parent": "integer",
  "parent_name": "string",
  "organization": "integer"
}
```

### Document Tag Object
```json
{
  "id": "integer",
  "name": "string",
  "description": "string",
  "color": "string",
  "organization": "integer"
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