# Document Management API Documentation

## Overview
The Document Management API provides endpoints for managing documents, document versions, classifications, and tags. This API supports document versioning, branching, merging, and full-text search capabilities using Elasticsearch.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Documents

#### List Documents
```http
GET /api/documents/
```
Returns a list of documents for the authenticated user.

**Query Parameters**
- `status`: Filter by document status (draft, review, approved, archived)
- `classification`: Filter by classification ID
- `tags`: Filter by tag IDs (comma-separated)
- `search`: Search in document title and description
- `ordering`: Sort by field (e.g., title, created_at, updated_at)
- `page`: Page number for pagination
- `page_size`: Number of items per page

**Response**
```json
{
  "count": 10,
  "next": "http://api.example.org/documents/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Project Proposal",
      "description": "Initial project proposal document",
      "status": "draft",
      "file": "http://example.com/media/documents/2024/04/18/1/proposal.pdf",
      "user": 1,
      "classification": 1,
      "tags": [1, 2],
      "created_at": "2024-04-18T10:00:00Z",
      "updated_at": "2024-04-18T10:00:00Z"
    }
  ]
}
```

#### Create Document
```http
POST /api/documents/
```
Create a new document.

**Request Body (multipart/form-data)**
```
title: Project Proposal
description: Initial project proposal document
status: draft
file: [file upload]
classification: 1
tags: [1, 2]
```

**Response**
```json
{
  "id": 1,
  "title": "Project Proposal",
  "description": "Initial project proposal document",
  "status": "draft",
  "file": "http://example.com/media/documents/2024/04/18/1/proposal.pdf",
  "user": 1,
  "classification": 1,
  "tags": [1, 2],
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T10:00:00Z"
}
```

#### Get Document
```http
GET /api/documents/{id}/
```
Returns a specific document.

**Response**
```json
{
  "id": 1,
  "title": "Project Proposal",
  "description": "Initial project proposal document",
  "status": "draft",
  "file": "http://example.com/media/documents/2024/04/18/1/proposal.pdf",
  "user": 1,
  "classification": 1,
  "tags": [1, 2],
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T10:00:00Z"
}
```

#### Update Document
```http
PUT /api/documents/{id}/
```
Update a document.

**Request Body (multipart/form-data)**
```
title: Updated Project Proposal
description: Updated project proposal document
status: review
file: [file upload]
classification: 2
tags: [1, 3]
```

**Response**
```json
{
  "id": 1,
  "title": "Updated Project Proposal",
  "description": "Updated project proposal document",
  "status": "review",
  "file": "http://example.com/media/documents/2024/04/18/1/updated_proposal.pdf",
  "user": 1,
  "classification": 2,
  "tags": [1, 3],
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T11:00:00Z"
}
```

#### Delete Document
```http
DELETE /api/documents/{id}/
```
Soft delete a document (sets is_deleted flag to true).

**Response**
```
204 No Content
```

#### Search Documents
```http
GET /api/documents/search/
```
Search documents using Elasticsearch.

**Query Parameters**
- `q`: Search query
- `filters`: JSON string of filters (e.g., {"status": "draft", "user_id": 1})
- `page`: Page number for pagination
- `page_size`: Number of items per page

**Response**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Project Proposal",
      "description": "Initial project proposal document",
      "status": "draft",
      "file": "http://example.com/media/documents/2024/04/18/1/proposal.pdf",
      "user": 1,
      "classification": 1,
      "tags": [1, 2],
      "created_at": "2024-04-18T10:00:00Z",
      "updated_at": "2024-04-18T10:00:00Z"
    }
  ]
}
```

### Document Versions

#### List Document Versions
```http
GET /api/documents/{document_id}/versions/
```
Returns a list of versions for a specific document.

**Response**
```json
[
  {
    "id": 1,
    "document": 1,
    "version_number": 1,
    "file": "http://example.com/media/documents/versions/2024/04/18/1/v1_proposal.pdf",
    "user": 1,
    "comment": "Initial version",
    "is_current": true,
    "branch_name": "main",
    "parent_version": null,
    "merged_to": null,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  },
  {
    "id": 2,
    "document": 1,
    "version_number": 2,
    "file": "http://example.com/media/documents/versions/2024/04/18/1/v2_proposal.pdf",
    "user": 1,
    "comment": "Updated with feedback",
    "is_current": false,
    "branch_name": "main",
    "parent_version": 1,
    "merged_to": null,
    "created_at": "2024-04-18T11:00:00Z",
    "updated_at": "2024-04-18T11:00:00Z"
  }
]
```

#### Create Document Version
```http
POST /api/documents/{document_id}/versions/
```
Create a new version of a document.

**Request Body (multipart/form-data)**
```
file: [file upload]
comment: Updated with feedback
branch_name: main
```

**Response**
```json
{
  "id": 2,
  "document": 1,
  "version_number": 2,
  "file": "http://example.com/media/documents/versions/2024/04/18/1/v2_proposal.pdf",
  "user": 1,
  "comment": "Updated with feedback",
  "is_current": true,
  "branch_name": "main",
  "parent_version": 1,
  "merged_to": null,
  "created_at": "2024-04-18T11:00:00Z",
  "updated_at": "2024-04-18T11:00:00Z"
}
```

#### Get Document Version
```http
GET /api/documents/{document_id}/versions/{version_id}/
```
Returns a specific document version.

**Response**
```json
{
  "id": 2,
  "document": 1,
  "version_number": 2,
  "file": "http://example.com/media/documents/versions/2024/04/18/1/v2_proposal.pdf",
  "user": 1,
  "comment": "Updated with feedback",
  "is_current": true,
  "branch_name": "main",
  "parent_version": 1,
  "merged_to": null,
  "created_at": "2024-04-18T11:00:00Z",
  "updated_at": "2024-04-18T11:00:00Z"
}
```

#### Create Branch
```http
POST /api/documents/{document_id}/versions/{version_id}/branch/
```
Create a new branch from a specific version.

**Request Body**
```json
{
  "branch_name": "feature-branch",
  "comment": "Creating feature branch"
}
```

**Response**
```json
{
  "id": 3,
  "document": 1,
  "version_number": 1,
  "file": "http://example.com/media/documents/versions/2024/04/18/1/v1_proposal.pdf",
  "user": 1,
  "comment": "Creating feature branch",
  "is_current": false,
  "branch_name": "feature-branch",
  "parent_version": 1,
  "merged_to": null,
  "created_at": "2024-04-18T12:00:00Z",
  "updated_at": "2024-04-18T12:00:00Z"
}
```

#### Merge Branch
```http
POST /api/documents/{document_id}/versions/{source_version_id}/merge/
```
Merge a branch into another branch.

**Request Body**
```json
{
  "target_version_id": 2,
  "comment": "Merging feature branch into main"
}
```

**Response**
```json
{
  "id": 4,
  "document": 1,
  "version_number": 3,
  "file": "http://example.com/media/documents/versions/2024/04/18/1/merged_proposal.pdf",
  "user": 1,
  "comment": "Merging feature branch into main",
  "is_current": true,
  "branch_name": "main",
  "parent_version": 2,
  "merged_to": null,
  "created_at": "2024-04-18T13:00:00Z",
  "updated_at": "2024-04-18T13:00:00Z"
}
```

#### Compare Versions
```http
GET /api/documents/{document_id}/versions/compare/
```
Compare two versions of a document.

**Query Parameters**
- `version1`: First version ID
- `version2`: Second version ID

**Response**
```json
{
  "version_numbers": [1, 2],
  "creation_times": ["2024-04-18T10:00:00Z", "2024-04-18T11:00:00Z"],
  "file_sizes": [1024, 2048],
  "comments": ["Initial version", "Updated with feedback"],
  "users": [1, 1]
}
```

#### Restore Version
```http
POST /api/documents/{document_id}/versions/{version_id}/restore/
```
Restore a document to a previous version.

**Response**
```json
{
  "id": 1,
  "title": "Project Proposal",
  "description": "Initial project proposal document",
  "status": "draft",
  "file": "http://example.com/media/documents/versions/2024/04/18/1/v1_proposal.pdf",
  "user": 1,
  "classification": 1,
  "tags": [1, 2],
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T14:00:00Z"
}
```

### Document Classifications

#### List Classifications
```http
GET /api/documents/classifications/
```
Returns a list of document classifications.

**Response**
```json
[
  {
    "id": 1,
    "name": "Project Documents",
    "description": "Documents related to projects",
    "parent": null,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Technical Specifications",
    "description": "Technical specification documents",
    "parent": 1,
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Classification
```http
POST /api/documents/classifications/
```
Create a new document classification.

**Request Body**
```json
{
  "name": "Technical Specifications",
  "description": "Technical specification documents",
  "parent": 1
}
```

**Response**
```json
{
  "id": 2,
  "name": "Technical Specifications",
  "description": "Technical specification documents",
  "parent": 1,
  "created_at": "2024-04-18T10:00:00Z",
  "updated_at": "2024-04-18T10:00:00Z"
}
```

### Document Tags

#### List Tags
```http
GET /api/documents/tags/
```
Returns a list of document tags.

**Response**
```json
[
  {
    "id": 1,
    "name": "Important",
    "description": "Important documents",
    "color": "#FF0000",
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Draft",
    "description": "Draft documents",
    "color": "#00FF00",
    "created_at": "2024-04-18T10:00:00Z",
    "updated_at": "2024-04-18T10:00:00Z"
  }
]
```

#### Create Tag
```http
POST /api/documents/tags/
```
Create a new document tag.

**Request Body**
```json
{
  "name": "Important",
  "description": "Important documents",
  "color": "#FF0000"
}
```

**Response**
```json
{
  "id": 1,
  "name": "Important",
  "description": "Important documents",
  "color": "#FF0000",
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

### Documents
- Title is required
- Status must be one of: draft, review, approved, archived
- File must be a valid document file

### Document Versions
- Version number must be greater than 0
- Parent version must belong to the same document
- Merged to version must belong to the same document
- Only one version can be current within a branch

### Document Classifications
- Name is required and must be unique
- Parent must be a valid classification or null

### Document Tags
- Name is required and must be unique
- Color must be a valid hex color code

## Best Practices

1. **Document Management**
   - Use appropriate classifications and tags for better organization
   - Keep document titles descriptive and consistent
   - Update document status as it progresses through workflows

2. **Version Control**
   - Create new versions for significant changes
   - Use branches for experimental changes
   - Provide clear comments for each version
   - Merge branches when features are complete

3. **Search**
   - Use specific search terms for better results
   - Combine search with filters for targeted results
   - Use tags and classifications for broader categorization

4. **File Handling**
   - Upload files in appropriate formats
   - Keep file sizes reasonable for better performance
   - Use descriptive filenames 